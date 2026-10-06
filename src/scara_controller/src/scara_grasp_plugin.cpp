#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>

#include <cmath>
#include <functional>
#include <memory>
#include <utility>

namespace gazebo
{
class ScaraGraspPlugin : public WorldPlugin
{
public:
  void Load(physics::WorldPtr world, sdf::ElementPtr) override
  {
    world_ = std::move(world);
    update_connection_ = event::Events::ConnectWorldUpdateBegin(
      std::bind(&ScaraGraspPlugin::OnUpdate, this));
    gzmsg << "SCARA grasp plugin ready" << std::endl;
  }

private:
  void OnUpdate()
  {
    auto robot = world_->ModelByName("scara");
    auto box = world_->ModelByName("caixa_a");
    if (!robot || !box) {
      return;
    }

    auto gripper = robot->GetLink("g1_gripper");
    auto finger_joint = robot->GetJoint("gripper_joint1");
    auto box_link = box->GetLink("link");
    if (!gripper || !finger_joint || !box_link) {
      return;
    }

    const double closure = finger_joint->Position(0);
    if (grasp_joint_) {
      if (closure < 0.002) {
        grasp_joint_->Detach();
        grasp_joint_->Fini();
        grasp_joint_.reset();
        gzmsg << "SCARA released caixa_a" << std::endl;
      }
      return;
    }

    // The finger centers are 41.75 mm below the g1_gripper link origin.
    const auto gripper_pos = gripper->WorldPose().Pos();
    const auto box_pos = box_link->WorldPose().Pos();
    const double dx = gripper_pos.X() - box_pos.X();
    const double dy = gripper_pos.Y() - box_pos.Y();
    const double dz = gripper_pos.Z() - 0.04175 - box_pos.Z();
    const double planar_distance = std::hypot(dx, dy);

    if (closure >= 0.0045 && planar_distance < 0.025 && std::abs(dz) < 0.025) {
      grasp_joint_ = world_->Physics()->CreateJoint("fixed", robot);
      grasp_joint_->SetName("scara_box_grasp");
      grasp_joint_->Load(gripper, box_link, ignition::math::Pose3d::Zero);
      grasp_joint_->Init();
      gzmsg << "SCARA grasped caixa_a" << std::endl;
    }
  }

  physics::WorldPtr world_;
  event::ConnectionPtr update_connection_;
  physics::JointPtr grasp_joint_;
};

GZ_REGISTER_WORLD_PLUGIN(ScaraGraspPlugin)
}  // namespace gazebo
