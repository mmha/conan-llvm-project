from conans import ConanFile, CMake, tools
import os


class PythonRequires(ConanFile):
    name = "llvm-project"
    version = "0.1"

def llvm_base_project():
    class BaseLLVMProject(ConanFile):
        @property
        def source_subfolder(self):
            return self.source_folder

        @property
        def cmake_option_prefix(self):
            return self.name.upper().replace("-", "_")

        settings = (
            "os",
            # "os_target",
            "compiler",
            "build_type",
            "arch",
            # "arch_target",
        )

        generators = "cmake"

        def config_options(self):
            if hasattr(self.settings, "os") and hasattr(self.options, "fPIC"):
                if self.settings.os == "Windows":
                    del self.options.fPIC
        
        def _llvm_cmake_definitions(self, options, prefix):
            """
            Translate the conan options to LLVM CMake options
            Prepend with a prefix and upper case the options
            """
            get_option = lambda o: {
                "True": "ON",
                "False": "OFF"
            }.get(o, o)

            definitions = {}

            for k, v in self.options.items():
                if k in options and v != "":
                    definitions[f"{prefix}_{k.upper()}"] = get_option(v)

            return definitions

        def configure_cmake(self):
            cmake = CMake(self)
            cmake.definitions["CONAN_LLVM_PROEJCT_DIR"] = self.source_subfolder
            if hasattr(self, "llvm_cmake_options"):
                cmake.definitions.update(self._llvm_cmake_definitions(self.llvm_cmake_options, self.cmake_option_prefix))
            if hasattr(self.options, "fPIC"):
                cmake.definitions["LLVM_ENABLE_PIC"] = self.options.fPIC
            if hasattr(self, "custom_cmake_definitions"):
                cmake.definitions.update(self.custom_cmake_definitions)
            cmake.configure(source_folder=self.source_subfolder(), build_folder="build_folder")
            return cmake

        _cmake = None
        @property
        def cmake(self):
            if self._cmake is None:
                self._cmake = self.configure_cmake()
            return self._cmake
        
        def build(self):
            cml = os.path.join(self.build_folder, "CMakeLists.txt")
            with open(cml, "w") as f:
                f.write("cmake_minimum_required(VERSION 3.4.3)\n")
                f.write("enable_language(C)\n")
                f.write("enable_language(CXX)\n")
                f.write("include(\"" + self.build_folder + "/conanbuildinfo.cmake\")\n")
                f.write("conan_basic_setup(TARGETS NO_OUTPUT_DIRS)\n")
                f.write(f"add_subdirectory({self.source_subfolder()})")
            self.cmake.build()
            if tools.get_env("CONAN_RUN_TESTS", True) and getattr(self.options, "build_tests", False):
                cmake.test(target=tools.get_env("LLVM_TEST_TARGET", "check-all"))

        def package(self):
            self.cmake.install()

        def package_info(self):
            self.user_info.cmake_option_prefix = self.cmake_option_prefix
            self.user_info.llvm_cmake_options = self.llvm_cmake_options

            bindir = os.path.join(self.package_folder, "bin")
            if os.path.isdir(bindir):
                self.output.info(f"Appending {self.name} to PATH environment variable: {bindir}")
                self.env_info.PATH.append(bindir)

    return BaseLLVMProject
