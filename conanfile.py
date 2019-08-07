from conans import AutoToolsBuildEnvironment, ConanFile, tools
import os
import platform

class CurlConan(ConanFile):
    name = 'curl'

    source_version = '7.65.3'
    package_version = '0'
    version = '%s-%s' % (source_version, package_version)

    build_requires = 'llvm/3.3-5@vuo/stable'
    requires = 'openssl/1.1.1c-0@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://curl.haxx.se/'
    license = 'https://curl.haxx.se/docs/copyright.html'
    description = 'A library for transferring data with URLs'
    source_dir = 'curl-%s' % source_version
    build_dir = '_build'
    install_dir = '_install'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        tools.get('http://curl.haxx.se/download/curl-%s.tar.gz' % self.source_version,
                  sha256='4376ac72b95572fb6c4fbffefb97c7ea0dd083e1974c0e44cd7e49396f454839')

        self.run('mv %s/COPYING %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)

            # The LLVM/Clang libs get automatically added by the `requires` line,
            # but this package doesn't need to link with them.
            autotools.libs = ['c++abi']

            autotools.flags.append('-Oz')

            # Hide all non-cURL symbols, for compliance with the
            # Export Administration Regulations of the U.S. Bureau of Industry and Security
            # (since we link to OpenSSL).
            if platform.system() == 'Darwin':
                autotools.link_flags.append("-Wl,-exported_symbol,'_curl*'")
            elif platform.system() == 'Linux':
                autotools.link_flags.append('-Wl,--exclude-libs=ALL')

            if platform.system() == 'Darwin':
                autotools.flags.append('-isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk')
                autotools.flags.append('-mmacosx-version-min=10.10')
                autotools.link_flags.append('-Wl,-headerpad_max_install_names')
                autotools.link_flags.append('-Wl,-install_name,@rpath/libcurl.dylib')
            elif platform.system() == 'Linux':
                autotools.libs.append('dl')

            env_vars = {
                'CC' : self.deps_cpp_info['llvm'].rootpath + '/bin/clang',
                'CXX': self.deps_cpp_info['llvm'].rootpath + '/bin/clang++',
            }
            with tools.environment_append(env_vars):
                autotools.configure(configure_dir='../%s' % self.source_dir,
                                    build=False,
                                    host=False,
                                    args=['--quiet',
                                          '--disable-ldap',
                                          '--enable-shared',
                                          '--with-ssl=' + self.deps_cpp_info['openssl'].rootpath,
                                          '--without-libidn',
                                          '--without-librtmp',
                                          '--without-libssh2',
                                          '--prefix=%s/../%s' % (os.getcwd(), self.install_dir)])
                autotools.make(args=['--quiet'])
                autotools.make(target='install', args=['--quiet'])

        with tools.chdir(self.install_dir):
            if platform.system() == 'Linux':
                patchelf = self.deps_cpp_info['patchelf'].rootpath + '/bin/patchelf'
                self.run('%s --set-soname libcurl.so lib/libcurl.so' % patchelf)

    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'

        self.copy('*.h', src='%s/include' % self.install_dir, dst='include')
        self.copy('libcurl.%s' % libext, src='%s/lib' % self.install_dir, dst='lib')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['curl']
