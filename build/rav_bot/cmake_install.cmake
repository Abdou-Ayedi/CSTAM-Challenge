# Install script for directory: /home/abdou/ros2_ws/src/rav_bot

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/abdou/ros2_ws/src/rav_bot/install/rav_bot")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE DIRECTORY FILES
    "/home/abdou/ros2_ws/src/rav_bot/rviz"
    "/home/abdou/ros2_ws/src/rav_bot/urdf"
    "/home/abdou/ros2_ws/src/rav_bot/launch"
    "/home/abdou/ros2_ws/src/rav_bot/world"
    "/home/abdou/ros2_ws/src/rav_bot/model"
    "/home/abdou/ros2_ws/src/rav_bot/script"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/config" TYPE DIRECTORY FILES "/home/abdou/ros2_ws/src/rav_bot/config/")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/rav_bot" TYPE PROGRAM FILES "/home/abdou/ros2_ws/src/rav_bot/script/joystick_control.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/rav_bot" TYPE PROGRAM FILES "/home/abdou/ros2_ws/src/rav_bot/script/multipoint_follow.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/rav_bot" TYPE PROGRAM FILES "/home/abdou/ros2_ws/src/rav_bot/script/point_follow.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/rav_bot" TYPE PROGRAM FILES "/home/abdou/ros2_ws/src/rav_bot/script/ultrasonic_sensor_obstacle_avoidance.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/rav_bot" TYPE PROGRAM FILES
    "/home/abdou/ros2_ws/src/rav_bot/script/auto_docking.py"
    "/home/abdou/ros2_ws/src/rav_bot/script/elevator.py"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/package_run_dependencies" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_index/share/ament_index/resource_index/package_run_dependencies/rav_bot")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/parent_prefix_path" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_index/share/ament_index/resource_index/parent_prefix_path/rav_bot")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/environment" TYPE FILE FILES "/opt/ros/humble/share/ament_cmake_core/cmake/environment_hooks/environment/ament_prefix_path.sh")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/environment" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/ament_prefix_path.dsv")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/environment" TYPE FILE FILES "/opt/ros/humble/share/ament_cmake_core/cmake/environment_hooks/environment/path.sh")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/environment" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/path.dsv")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/local_setup.bash")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/local_setup.sh")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/local_setup.zsh")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/local_setup.dsv")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_environment_hooks/package.dsv")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/packages" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_index/share/ament_index/resource_index/packages/rav_bot")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot/cmake" TYPE FILE FILES
    "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_core/rav_botConfig.cmake"
    "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/ament_cmake_core/rav_botConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/rav_bot" TYPE FILE FILES "/home/abdou/ros2_ws/src/rav_bot/package.xml")
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/abdou/ros2_ws/src/rav_bot/build/rav_bot/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
