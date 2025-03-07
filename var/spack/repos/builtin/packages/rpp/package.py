# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *
from spack.pkg.builtin.boost import Boost


class Rpp(CMakePackage):
    """Radeon Performance Primitives (RPP) library is a comprehensive high-
    performance computer vision library for AMD (CPU and GPU) with HIP
    and OPENCL back-ends"""

    homepage = "https://github.com/GPUOpen-ProfessionalCompute-Libraries/rpp"
    git = "https://github.com/GPUOpen-ProfessionalCompute-Libraries/rpp.git"
    url = "https://github.com/GPUOpen-ProfessionalCompute-Libraries/rpp/archive/refs/tags/rocm-5.7.0.tar.gz"

    def url_for_version(self, version):
        if version >= Version("5.7.0"):
            url = "https://github.com/GPUOpen-ProfessionalCompute-Libraries/rpp/archive/refs/tags/rocm-{0}.tar.gz"
        else:
            url = "https://github.com/GPUOpen-ProfessionalCompute-Libraries/rpp/archive/{0}.tar.gz"
        return url.format(version)

    maintainers = ["srekolam", "afzpatel"]
    tags = ["rocm"]

    license("MIT")

    version("5.7.1", sha256="36fff5f1c52d969c3e2e0c75b879471f731770f193c9644aa6ab993fb8fa4bbf")
    version("5.7.0", sha256="1c612cde3c3d3840ae75ee5c1ee59bd8d61b1fdbf84421ae535cda863470fc06")
    version("1.2.0", sha256="660a11e1bd8706967835597b26daa874fd1507459bfebe22818149444bec540c")
    version("1.1.0", sha256="9b1b9e721df27ee577819710b261071c68b2dccba96d9daf5d0535ee5f0e045f")
    version("1.0.0", sha256="040601e356b0a06c4ffb2043320ae822ab0da78af867392002c7b68dbd85989c")
    version("0.99", sha256="f1d7ec65d0148ddb7b3ce836a7e058727036df940d72d1683dee590a913fd44a")
    version("0.98", sha256="191b5d89bf990ae22b5ef73675b89ed4371c3ce342ab9cc65383fa12ef13086e")
    version("0.97", sha256="8ce1a869ff67a29579d87d399d8b0bd97bf12ae1b6b1ca1f161cb8a262fb9939")
    variant(
        "build_type",
        default="Release",
        values=("Release", "Debug", "RelWithDebInfo"),
        description="CMake build type",
    )
    # Adding 3 variants OPENCL ,HIP , CPU with HIP as default.

    variant("opencl", default=False, description="Use OPENCL as the backend")
    variant("hip", default=True, description="Use HIP as backend")
    variant("cpu", default=False, description="Use CPU as backend")
    variant(
        "add_tests",
        default=False,
        description="add utilities folder which contains rpp unit tests",
    )

    patch("0001-include-half-openmp-through-spack-package.patch")
    patch("0002-declare-handle-in-header.patch")

    # adds half.hpp include directory and modifies how the libjpegturbo
    # library is linked for the rpp unit test
    patch("0003-changes-to-rpp-unit-tests.patch", when="+add_tests")

    def patch(self):
        if self.spec.satisfies("+hip"):
            filter_file(
                "${ROCM_PATH}/llvm", self.spec["llvm-amdgpu"].prefix, "CMakeLists.txt", string=True
            )
        if self.spec.satisfies("+opencl"):
            filter_file(
                "${ROCM_PATH}",
                self.spec["rocm-opencl"].prefix,
                "cmake/FindOpenCL.cmake",
                string=True,
            )
        if self.spec.satisfies("+add_tests"):
            filter_file(
                "${ROCM_PATH}/include/rpp",
                self.spec.prefix.include.rpp,
                "utilities/test_suite/HOST/CMakeLists.txt",
                string=True,
            )
            filter_file(
                "${ROCM_PATH}/lib",
                self.spec.prefix.lib,
                "utilities/test_suite/HOST/CMakeLists.txt",
                string=True,
            )
            filter_file(
                "${ROCM_PATH}/include/rpp",
                self.spec.prefix.include.rpp,
                "utilities/test_suite/HIP/CMakeLists.txt",
                string=True,
            )
            filter_file(
                "${ROCM_PATH}/lib",
                self.spec.prefix.lib,
                "utilities/test_suite/HIP/CMakeLists.txt",
                string=True,
            )

    depends_on("cmake@3.5:", type="build")
    depends_on("pkgconfig", type="build")
    depends_on(Boost.with_default_variants)
    depends_on("boost@1.72.0:1.80.0")
    depends_on("bzip2")
    depends_on("half")
    depends_on("hwloc")
    depends_on(
        "opencv@4.5:"
        "+calib3d+features2d+highgui+imgcodecs+imgproc"
        "+video+videoio+flann+photo+objdetect",
        type=("build", "link"),
        when="@1.0:",
    )
    depends_on("libjpeg-turbo", type=("build", "link"))
    depends_on("rocm-openmp-extras")
    conflicts("+opencl+hip")

    with when("+hip"):
        depends_on("hip@5:")
    with when("~hip"):
        depends_on("rocm-opencl@5:")

    def setup_run_environment(self, env):
        if self.spec.satisfies("+add_tests"):
            env.set("TURBO_JPEG_PATH", self.spec["libjpeg-turbo"].prefix)

    def cmake_args(self):
        spec = self.spec
        args = []
        args.append(self.define("ROCM_OPENMP_EXTRAS_DIR", spec["rocm-openmp-extras"].prefix))
        if self.spec.satisfies("+opencl"):
            args.append(self.define("BACKEND", "OPENCL"))
        if self.spec.satisfies("+cpu"):
            args.append(self.define("BACKEND", "CPU"))
        if self.spec.satisfies("+hip"):
            args.append(self.define("BACKEND", "HIP"))
            args.append(self.define("HIP_PATH", spec["hip"].prefix))
            args.append(
                self.define(
                    "COMPILER_FOR_HIP", "{0}/bin/clang++".format(spec["llvm-amdgpu"].prefix)
                )
            )
        return args

    @run_after("install")
    def add_tests(self):
        if self.spec.satisfies("+add_tests"):
            install_tree("utilities", self.spec.prefix.utilities)
            install_tree("cmake", self.spec.prefix.cmake)
