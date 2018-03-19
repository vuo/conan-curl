from conans import AutoToolsBuildEnvironment, ConanFile, tools
import os
import platform

class CurlConan(ConanFile):
    name = 'curl'

    source_version = '7.30.0'
    package_version = '1'
    version = '%s-%s' % (source_version, package_version)

    requires = 'llvm/3.3-1@vuo/stable', \
        'openssl/1.0.2n-1@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://curl.haxx.se/'
    license = 'https://curl.haxx.se/docs/copyright.html'
    description = 'A library for transferring data with URLs'
    source_dir = 'curl-%s' % source_version
    build_dir = '_build'
    install_dir = '_install'

    def source(self):
        tools.get('http://curl.haxx.se/download/curl-%s.tar.gz' % self.source_version,
                  sha256='361669c3c4b9baa5343e7e83bce695e60683d0b97b402e664bbaed42c15e95a8')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)

            # The LLVM/Clang libs get automatically added by the `requires` line,
            # but this package doesn't need to link with them.
            autotools.libs = []

            autotools.cxx_flags.append('-Oz')

            if platform.system() == 'Darwin':
                autotools.cxx_flags.append('-mmacosx-version-min=10.10')
                autotools.link_flags.append('-Wl,-headerpad_max_install_names')
                autotools.link_flags.append('-Wl,-install_name,@rpath/libcurl.dylib')

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
                                          '--with-ssl',
                                          '--without-libidn',
                                          '--without-librtmp',
                                          '--without-libssh2',
                                          '--prefix=%s/../%s' % (os.getcwd(), self.install_dir)])
                autotools.make(args=['--quiet'])
                autotools.make(target='install', args=['--quiet'])

    def package(self):
        self.copy('*.h', src='%s/include' % self.install_dir, dst='include')
        self.copy('libcurl.dylib', src='%s/lib' % self.install_dir, dst='lib')

    def package_info(self):
        self.cpp_info.libs = ['curl']
