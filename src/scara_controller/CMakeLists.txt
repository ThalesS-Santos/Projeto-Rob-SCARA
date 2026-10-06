cmake_minimum_required(VERSION 3.8)
project(scara_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(gazebo REQUIRED)

add_library(scara_grasp_plugin SHARED src/scara_grasp_plugin.cpp)
target_include_directories(scara_grasp_plugin PRIVATE ${GAZEBO_INCLUDE_DIRS})
target_link_libraries(scara_grasp_plugin ${GAZEBO_LIBRARIES})
target_compile_options(scara_grasp_plugin PRIVATE ${GAZEBO_CXX_FLAGS})

install(TARGETS scara_grasp_plugin
  LIBRARY DESTINATION lib
)

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/slider_control.py
    scripts/pick_and_place.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
