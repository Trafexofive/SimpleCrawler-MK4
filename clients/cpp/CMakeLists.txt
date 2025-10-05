cmake_minimum_required(VERSION 3.16)
project(SimpleCrawlerClient 
    VERSION 2.0.0 
    DESCRIPTION "Professional C++ client library for SimpleCrawler MK4"
    LANGUAGES CXX
)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build options
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_EXAMPLES "Build example programs" ON)
option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

# Find dependencies
find_package(PkgConfig REQUIRED)

# Find libcurl
find_package(CURL REQUIRED)

# Find nlohmann/json
find_package(nlohmann_json 3.11.0 REQUIRED)

# Optional: Find OpenSSL for HTTPS support
find_package(OpenSSL)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CURL_INCLUDE_DIRS}
)

# Compiler flags
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -DNDEBUG")
endif()

# Source files
set(SOURCES
    src/client.cpp
    src/http_client.cpp
    src/json_utils.cpp
    src/models.cpp
    src/exceptions.cpp
)

# Header files
set(HEADERS
    include/simplecrawler/client.hpp
    include/simplecrawler/http_client.hpp
    include/simplecrawler/json_utils.hpp
    include/simplecrawler/models.hpp
    include/simplecrawler/exceptions.hpp
    include/simplecrawler/version.hpp
)

# Create library
if(BUILD_SHARED_LIBS)
    add_library(${PROJECT_NAME} SHARED ${SOURCES} ${HEADERS})
else()
    add_library(${PROJECT_NAME} STATIC ${SOURCES} ${HEADERS})
endif()

# Set library properties
set_target_properties(${PROJECT_NAME} PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    PUBLIC_HEADER "${HEADERS}"
)

# Link libraries
target_link_libraries(${PROJECT_NAME}
    PUBLIC
        ${CURL_LIBRARIES}
        nlohmann_json::nlohmann_json
)

if(OpenSSL_FOUND)
    target_link_libraries(${PROJECT_NAME} PUBLIC OpenSSL::SSL OpenSSL::Crypto)
    target_compile_definitions(${PROJECT_NAME} PRIVATE SIMPLECRAWLER_HAVE_OPENSSL)
endif()

# Include directories for target
target_include_directories(${PROJECT_NAME}
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Compile definitions
target_compile_definitions(${PROJECT_NAME}
    PRIVATE
        SIMPLECRAWLER_VERSION="${PROJECT_VERSION}"
        SIMPLECRAWLER_VERSION_MAJOR=${PROJECT_VERSION_MAJOR}
        SIMPLECRAWLER_VERSION_MINOR=${PROJECT_VERSION_MINOR}
        SIMPLECRAWLER_VERSION_PATCH=${PROJECT_VERSION_PATCH}
)

# Examples
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# Testing
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
include(GNUInstallDirs)

install(TARGETS ${PROJECT_NAME}
    EXPORT SimpleCrawlerClientTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/simplecrawler
)

# Install headers
install(DIRECTORY include/simplecrawler
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING PATTERN "*.hpp"
)

# Export targets
install(EXPORT SimpleCrawlerClientTargets
    FILE SimpleCrawlerClientTargets.cmake
    NAMESPACE SimpleCrawler::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/SimpleCrawlerClient
)

# Generate config file
include(CMakePackageConfigHelpers)

configure_package_config_file(
    cmake/SimpleCrawlerClientConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/SimpleCrawlerClientConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/SimpleCrawlerClient
)

write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/SimpleCrawlerClientConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/SimpleCrawlerClientConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/SimpleCrawlerClientConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/SimpleCrawlerClient
)

# pkg-config file
configure_file(
    cmake/simplecrawler-client.pc.in
    ${CMAKE_CURRENT_BINARY_DIR}/simplecrawler-client.pc
    @ONLY
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/simplecrawler-client.pc
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig
)

# Print configuration summary
message(STATUS "SimpleCrawler C++ Client Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Build Tests: ${BUILD_TESTS}")
message(STATUS "  Build Examples: ${BUILD_EXAMPLES}")
message(STATUS "  Build Shared: ${BUILD_SHARED_LIBS}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "  CURL Found: ${CURL_FOUND}")
message(STATUS "  nlohmann/json Found: ${nlohmann_json_FOUND}")
message(STATUS "  OpenSSL Found: ${OpenSSL_FOUND}")