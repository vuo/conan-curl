from conans import ConanFile, CMake, tools
import os
import platform

class CurlConan(ConanFile):
    name = 'curl'

    source_version = '7.73.0'
    package_version = '0'
    version = '%s-%s' % (source_version, package_version)

    build_requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )
    requires = 'openssl/1.1.1h-0@vuo/stable'
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
                  sha256='ba98332752257b47b9dea6d8c0ad25ec1745c20424f1dd3ff2c99ab59e97cf91')

        self.run('mv %s/COPYING %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        cmake = CMake(self)

        cmake.definitions['CMAKE_BUILD_TYPE'] = 'Release'
        cmake.definitions['CMAKE_C_COMPILER']   = '%s/bin/clang'   % self.deps_cpp_info['llvm'].rootpath
        cmake.definitions['CMAKE_C_FLAGS'] = '-Oz'
        cmake.definitions['CMAKE_INSTALL_NAME_DIR'] = '@rpath'
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = '%s/%s' % (os.getcwd(), self.install_dir)
        cmake.definitions['CMAKE_OSX_ARCHITECTURES'] = 'x86_64;arm64'
        cmake.definitions['CMAKE_OSX_DEPLOYMENT_TARGET'] = '10.11'
        cmake.definitions['CMAKE_OSX_SYSROOT'] = self.deps_cpp_info['macos-sdk'].rootpath
        cmake.definitions['BUILD_SHARED_LIBS'] = 'ON'
        cmake.definitions['BUILD_STATIC_LIBS'] = 'OFF'
        cmake.definitions['BUILD_CURL_EXE'] = 'OFF'
        cmake.definitions['CURL_DISABLE_LDAP'] = 'ON'
        cmake.definitions['CURL_DISABLE_LDAPS'] = 'ON'
        cmake.definitions['CURL_DISABLE_GOPHER'] = 'ON'
        cmake.definitions['CURL_DISABLE_IMAP'] = 'ON'
        cmake.definitions['CURL_DISABLE_MQTT'] = 'ON'
        cmake.definitions['CURL_DISABLE_POP3'] = 'ON'
        cmake.definitions['CURL_DISABLE_PROXY'] = 'ON'
        cmake.definitions['CURL_DISABLE_RTSP'] = 'ON'
        cmake.definitions['CURL_DISABLE_SMTP'] = 'ON'
        cmake.definitions['CURL_DISABLE_TELNET'] = 'ON'
        cmake.definitions['CURL_DISABLE_TFTP'] = 'ON'
        cmake.definitions['CMAKE_USE_LIBSSH2'] = 'OFF'
        cmake.definitions['OPENSSL_ROOT_DIR'] = self.deps_cpp_info['openssl'].rootpath

        # Hide all non-cURL symbols, for compliance with the
        # Export Administration Regulations of the U.S. Bureau of Industry and Security
        # (since we link to OpenSSL).
        if platform.system() == 'Darwin':
            cmake.definitions['CMAKE_SHARED_LINKER_FLAGS'] = "-Wl,-exported_symbol,'_curl*'"
        elif platform.system() == 'Linux':
            cmake.definitions['CMAKE_SHARED_LINKER_FLAGS'] = '-Wl,--exclude-libs=ALL'

        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            cmake.configure(source_dir='../%s' % self.source_dir,
                            build_dir='.')
            cmake.build()
            cmake.install()

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
