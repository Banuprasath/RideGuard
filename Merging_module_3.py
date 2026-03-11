#!/usr/bin/env python

# CARLA Combined Control - Helmet Detection + Tilt Accident Simulation
# Integrates both Module 1 (Helmet Detection) and Module 2 (Tilt Accident) functionality

from __future__ import print_function

import glob
import os
import sys
import time
import cv2
import math
import random
import argparse
import weakref
import threading
import cv2
from ultralytics import YOLO
import emergency_alert  # Emergency alert module

# CARLA Setup
sys.path.append(
    r"D:\softwares\CARLA_0.9.10\WindowsNoEditor\PythonAPI\carla\dist\carla-0.9.10-py3.7-win-amd64.egg"
)

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

try:
    import pygame
    from pygame.locals import *
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

# ================= Configuration =================
def load_env_var(var_name, default_value):
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith(f'{var_name}='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        pass
    return default_value

ESP32_STREAM_URL = load_env_var('ESP32_STREAM_URL', 'http://192.168.137.63:81/stream')
FALL_FILE = r"d:\CEG-MCA\Semester-4\Final-Year-Project\Module-3-RearRecord\iot-python\fall_status.txt"
ACCIDENT_TRIGGER_FILE = "accident_trigger.txt"  # Same folder as this script
WARNING_TRIGGER_FILE = "rear_warning.txt"       # Warning signal file
HOTSPOT_WARNING_FILE = "hotspot_warning.txt"    # Hotspot warning file

# ================= Global Variables =================
# Helmet Detection
helmet_ok = False
last_helmet_check = 0
helmet_check_interval = 5.0  # Check every 5 seconds
model = None
cap = None

# Simplified detection variables
confidence_threshold = 0.25  # Very low threshold for maximum detection

# Tilt Detection
tilt_status = "NONE"
last_tilt_check = 0
tilt_check_interval = 5.0
startup_delay = 5.0
script_start_time = 0
last_accident_trigger_check = 0
accident_trigger_check_interval = 0.5  # Check every 0.5 seconds

# Module 3 - Rear Vehicle (Enhanced)
rear_vehicle = None
rear_collision_active = False
rear_collision_start_time = 0
rear_collision_duration = 2.5  # Extended for better animation
rear_collision_stage = "NONE"  # APPROACH, IMPACT, FALL
last_keyboard_direction = None  # Track last arrow key pressed

# ================= Helmet Detection Functions =================
def init_helmet_detection():
    """Initialize YOLO model and laptop webcam only"""
    global model, cap
    try:
        model = YOLO("best.pt")
        print("Helmet detection model loaded successfully!")
        print("Model classes:", model.names)
        
        # Use laptop webcam only
        print("Connecting to laptop webcam...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Warning: Could not open webcam - trying camera 1")
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                print("Warning: Could not open any camera - helmet detection disabled")
                cap = None
                model = None
                return False
            else:
                print("Using laptop webcam (camera 1)")
        else:
            print("Using laptop webcam (camera 0)")
        
        # Set camera properties for better detection
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)
        except:
            pass
        
        print("Camera initialized successfully")
        
        # Initial helmet check
        check_helmet()
        return True
    except Exception as e:
        print(f"Warning: Helmet detection disabled - {e}")
        model = None
        cap = None
        return False

def validate_detection(box, conf, class_name):
    """Simple validation matching webcam test"""
    return conf > confidence_threshold

def check_helmet():
    """Simple helmet detection - accept any detection above threshold"""
    global helmet_ok, cap, model
    
    if cap is None or model is None:
        return
    
    try:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to read frame from camera.", end="\r")
            return
        
        results = model(frame, verbose=False)
        
        helmet_found = False
        no_helmet_found = False
        best_conf = 0.0
        best_class = "None"
        
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls_id]
                
                if validate_detection(box, conf, class_name):
                    if conf > best_conf:
                        best_conf = conf
                        best_class = class_name
                    
                    if class_name == "With Helmet":
                        helmet_found = True
                    elif class_name == "Without Helmet":
                        no_helmet_found = True
        
        # Simple decision - any detection counts
        if helmet_found:
            helmet_ok = True
            print(f"✓ HELMET DETECTED - {best_class} @ {best_conf:.2f}")
        elif no_helmet_found:
            helmet_ok = False
            print(f"✗ NO HELMET - {best_class} @ {best_conf:.2f}")
        else:
            print(f"? NO DETECTION (keeping current: {'DETECTED' if helmet_ok else 'NOT DETECTED'})")
        
    except Exception as e:
        print(f"Error in helmet detection: {e}")

# ================= Tilt Detection Functions =================
def read_tilt_status():
    global tilt_status
    try:
        with open(FALL_FILE, "r") as f:
            status = f.read().strip().upper()
            print(f"[DEBUG] Read from fall_status.txt: '{status}'")
            if status in ["LEFT", "RIGHT", "NONE"]:
                tilt_status = status
            else:
                tilt_status = "NONE"
    except Exception as e:
        print(f"[DEBUG] Error reading fall_status.txt: {e}")
        tilt_status = "NONE"
    
    return tilt_status

def check_accident_trigger():
    """Check if hardware system detected accident"""
    try:
        if os.path.exists(ACCIDENT_TRIGGER_FILE):
            with open(ACCIDENT_TRIGGER_FILE, "r") as f:
                content = f.read().strip().upper()
                if content == "ACCIDENT":
                    print(f"\n[HARDWARE] ACCIDENT detected in trigger file!")
                    with open(ACCIDENT_TRIGGER_FILE, "w") as fw:
                        fw.write("")
                    return True
    except Exception as e:
        print(f"[ERROR] Reading trigger file: {e}")
    return False

def check_warning_trigger():
    """Check if hardware system detected proximity warning"""
    try:
        if os.path.exists(WARNING_TRIGGER_FILE):
            with open(WARNING_TRIGGER_FILE, "r") as f:
                content = f.read().strip().upper()
                if content == "WARNING":
                    return True
    except:
        pass
    return False

def check_hotspot_warning():
    """Check if vehicle is in accident-prone area"""
    try:
        if os.path.exists(HOTSPOT_WARNING_FILE):
            with open(HOTSPOT_WARNING_FILE, "r") as f:
                content = f.read().strip()
                if content.startswith("WARNING"):
                    parts = content.split("|")
                    if len(parts) == 3:
                        return True, int(parts[1]), float(parts[2])
    except:
        pass
    return False, 0, 0.0

# ================= CARLA World Class =================
class World(object):
    def __init__(self, carla_world, hud, args):
        self.world = carla_world
        self.actor_role_name = args.rolename
        
        # Clean up existing vehicles first
        print("[CLEANUP] Removing unwanted vehicles from world...")
        actors = self.world.get_actors().filter('vehicle.*')
        for actor in actors:
            actor.destroy()
        print(f"[CLEANUP] Removed {len(actors)} vehicles")
        
        # Asynchronous mode for smooth performance
        settings = self.world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = 0.0
        self.world.apply_settings(settings)
        
        self.map = self.world.get_map()
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.camera_manager = None
        self._gamma = args.gamma
        self.restart()
        self.world.on_tick(hud.on_world_tick)

    def restart(self):
        global rear_vehicle
        
        blueprint_library = self.world.get_blueprint_library()
        blueprint = random.choice(blueprint_library.filter('vehicle.yamaha.yzf'))
        blueprint.set_attribute('role_name', self.actor_role_name)
        
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        
        spawn_points = self.map.get_spawn_points()
        spawn_point = random.choice(spawn_points)
        print(f"[DEBUG] Selected spawn point: {spawn_point.location}")
        self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        
        if self.player is None:
            print('Failed to spawn vehicle')
            sys.exit(1)
        
        # Module 3: Spawn rear vehicle with guaranteed visibility
        print("[DEBUG] Spawning rear vehicle (Module 3 - Enhanced)...")
        
        # Use Tesla Model 3 for clear visibility with red color for emphasis
        rear_blueprint = blueprint_library.find('vehicle.tesla.model3')
        if not rear_blueprint:
            rear_blueprint = blueprint_library.find('vehicle.audi.a2')
        
        # Set a bright color for better visibility
        if rear_blueprint.has_attribute('color'):
            rear_blueprint.set_attribute('color', '255,0,0')  # Bright red
        
        print(f"[DEBUG] Using rear blueprint: {rear_blueprint.id}")
        
        # Wait for ego vehicle to be properly positioned
        time.sleep(0.2)
        ego_transform = self.player.get_transform()
        
        # Calculate rear position 10 meters behind ego (increased distance)
        forward_vector = ego_transform.get_forward_vector()
        rear_spawn = carla.Transform(
            carla.Location(
                x=ego_transform.location.x - (forward_vector.x * 10.0),
                y=ego_transform.location.y - (forward_vector.y * 10.0),
                z=ego_transform.location.z + 0.3
            ),
            ego_transform.rotation
        )
        
        print(f"[DEBUG] Rear spawn position: {rear_spawn.location}")
        
        # Try spawning at calculated position
        rear_vehicle = self.world.try_spawn_actor(rear_blueprint, rear_spawn)
        
        # If failed, try slightly offset positions
        if not rear_vehicle:
            for offset in [1.0, -1.0, 2.0, -2.0, 3.0]:
                adjusted_spawn = carla.Transform(
                    carla.Location(
                        x=rear_spawn.location.x + offset,
                        y=rear_spawn.location.y,
                        z=rear_spawn.location.z
                    ),
                    rear_spawn.rotation
                )
                rear_vehicle = self.world.try_spawn_actor(rear_blueprint, adjusted_spawn)
                if rear_vehicle:
                    print(f"[DEBUG] Rear vehicle spawned with offset {offset}m")
                    break
        
        if rear_vehicle:
            print(f"[TEST] Rear vehicle spawned successfully at 10m behind ego")
            print(f"[DEBUG] Rear vehicle ID: {rear_vehicle.id}")
            # Keep rear vehicle stationary initially
            rear_vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
        else:
            print("[ERROR] Failed to spawn rear vehicle!")
        
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        # Store reference to world in hud for camera switching
        self.hud.world = self
        
        self.hud.notification("Yamaha YZF Spawned - Enhanced Collision System Active!")

    def tick(self, clock):
        self.hud.tick(self, clock)

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy(self):
        global rear_vehicle
        print("[DEBUG] Destroying world actors...")
        if self.player is not None:
            self.player.destroy()
        if rear_vehicle is not None:
            print("[DEBUG] Destroying rear vehicle...")
            rear_vehicle.destroy()
            rear_vehicle = None
            print("[DEBUG] Rear vehicle destroyed")

# ================= Combined Control Class =================
class CombinedControl(object):
    def __init__(self, world):
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0
        self.world = world
        
        # Accident state
        self.accident_triggered = False
        self.accident_side = None
        self.accident_start_time = 0.0
        self.accident_duration = 3.0  # Extended for dramatic effect
        self.keyboard_accident_mode = False
        
        # Enhanced physics parameters
        self.impact_applied = False
        self.initial_velocity = None
        
        print("Combined Control Active - Enhanced Animation System")

    def trigger_accident(self, side, source="MPU"):
        if not self.accident_triggered:
            self.accident_triggered = True
            self.accident_side = side
            self.accident_start_time = time.time()
            self.keyboard_accident_mode = (source == "KEYBOARD")
            self.impact_applied = False
            
            # Store initial velocity for realistic physics
            v = self.world.player.get_velocity()
            self.initial_velocity = math.sqrt(v.x**2 + v.y**2 + v.z**2)
            
            self.world.hud.notification(f"⚠️ COLLISION! FALLING {side}! ({source}) ⚠️", seconds=5.0)
            print(f"⚠️ ACCIDENT TRIGGERED - FALL {side} - Source: {source}")
            
            # Log evidence ONLY for real accidents (not keyboard tests)
            if source != "KEYBOARD":
                print("[EVIDENCE] Triggering evidence logging...")
                try:
                    # Get CARLA location
                    carla_transform = self.world.player.get_transform()
                    
                    # Read ESP32 event name from shared file
                    esp32_event = None
                    try:
                        with open("latest_event.txt", "r") as f:
                            esp32_event = f.read().strip()
                            if esp32_event:
                                print(f"[EVIDENCE] Using ESP32 event: {esp32_event}")
                    except:
                        print("[DEBUG][EVIDENCE] No ESP32 event file found")
                    
                    # Log evidence (runs in background thread)
                    emergency_alert.log_accident_evidence(
                        carla_transform=carla_transform,
                        trigger_source=source,
                        esp32_event_name=esp32_event
                    )
                except Exception as e:
                    print(f"[ERROR][EVIDENCE] Failed to log evidence: {e}")
            else:
                # Keyboard test - write SENT immediately for acknowledgment
                try:
                    with open("telegram_status.txt", "w") as f:
                        f.write("SENT")
                except:
                    pass

    def update_accident_physics(self):
        """Enhanced accident physics with realistic fall animation"""
        vehicle = self.world.player
        elapsed = time.time() - self.accident_start_time
        progress = min(elapsed / self.accident_duration, 1.0)
        
        # Multi-stage fall animation
        if progress < 0.2:
            # Stage 1: Initial impact shock (0-0.6s)
            self._apply_impact_stage(vehicle, progress / 0.2)
        elif progress < 0.5:
            # Stage 2: Tilting and losing control (0.6-1.5s)
            self._apply_tilt_stage(vehicle, (progress - 0.2) / 0.3)
        else:
            # Stage 3: Complete fall (1.5-3.0s)
            self._apply_fall_stage(vehicle, (progress - 0.5) / 0.5)

    def _apply_impact_stage(self, vehicle, stage_progress):
        """Stage 1: Initial impact with sudden deceleration"""
        steer_direction = 1.0 if self.accident_side == "LEFT" else -1.0
        
        # FORCE stop all movement
        vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
        
        # Apply one-time impact force
        if not self.impact_applied:
            impact_impulse = carla.Vector3D(
                x=steer_direction * 500.0,  # Sideways push
                y=0,
                z=150.0  # Slight upward force
            )
            vehicle.add_impulse(impact_impulse)
            self.impact_applied = True
            print("[ANIMATION] Impact force applied!")
        
        # Full brake
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = 1.0
        control.hand_brake = True
        control.steer = steer_direction * 0.4 * stage_progress
        vehicle.apply_control(control)
        
        # FORCE rotation regardless of physics
        transform = vehicle.get_transform()
        transform.rotation.roll = steer_direction * 10.0 * stage_progress
        transform.rotation.pitch = 3.0 * stage_progress
        
        try:
            vehicle.set_transform(transform)
        except:
            pass

    def _apply_tilt_stage(self, vehicle, stage_progress):
        """Stage 2: Progressive tilting with loss of control"""
        steer_direction = 1.0 if self.accident_side == "LEFT" else -1.0
        
        # FORCE stop all movement
        vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
        
        # Smooth easing function for natural motion
        eased_progress = self._ease_in_out(stage_progress)
        
        # Full brake always
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = 1.0
        control.hand_brake = True
        control.steer = steer_direction * 0.8
        vehicle.apply_control(control)
        
        # FORCE dramatic tilting animation
        transform = vehicle.get_transform()
        max_tilt = 45.0  # Degrees
        transform.rotation.roll = steer_direction * max_tilt * eased_progress
        transform.rotation.pitch = 8.0 * eased_progress
        
        # Slight yaw for realism
        transform.rotation.yaw += steer_direction * 2.0 * stage_progress
        
        try:
            vehicle.set_transform(transform)
        except:
            pass

    def _apply_fall_stage(self, vehicle, stage_progress):
        """Stage 3: Complete fall to ground with sliding"""
        steer_direction = 1.0 if self.accident_side == "LEFT" else -1.0
        
        # FORCE stop all movement
        vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
        
        # Smooth easing for final fall
        eased_progress = self._ease_in(stage_progress)
        
        # Full brake and handbrake
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = 1.0
        control.hand_brake = True
        control.steer = steer_direction * 0.9
        vehicle.apply_control(control)
        
        # FORCE complete fall rotation
        transform = vehicle.get_transform()
        max_fall_roll = 75.0  # Reduced from 85 to prevent going through road
        transform.rotation.roll = steer_direction * (45.0 + (max_fall_roll - 45.0) * eased_progress)
        transform.rotation.pitch = 8.0 + (12.0 * eased_progress)
        
        # Keep vehicle slightly above ground to prevent clipping
        transform.location.z = max(transform.location.z, 0.5)
        
        try:
            vehicle.set_transform(transform)
        except:
            pass
        
        # Log completion
        if stage_progress > 0.95 and not hasattr(self, 'fall_completed'):
            self.fall_completed = True
            print("[ANIMATION] Fall sequence completed!")

    def _ease_in_out(self, t):
        """Smooth easing function for natural motion"""
        return t * t * (3.0 - 2.0 * t)
    
    def _ease_in(self, t):
        """Ease-in function for acceleration"""
        return t * t

    def update_rear_collision(self):
        """Enhanced rear vehicle collision with multi-stage animation"""
        global rear_vehicle, rear_collision_active, rear_collision_start_time, rear_collision_stage
        
        if not rear_collision_active or not rear_vehicle:
            return
        
        elapsed = time.time() - rear_collision_start_time
        
        # Calculate distance
        ego_loc = self.world.player.get_location()
        rear_loc = rear_vehicle.get_location()
        distance = math.sqrt((ego_loc.x - rear_loc.x)**2 + (ego_loc.y - rear_loc.y)**2)
        
        # Multi-stage collision animation
        if rear_collision_stage == "APPROACH":
            # Stage 1: Rear vehicle accelerates toward ego (0-1.5s)
            if elapsed < 1.5:
                # Progressive acceleration for dramatic effect
                throttle = min(0.5 + (elapsed * 0.3), 1.0)
                rear_vehicle.apply_control(carla.VehicleControl(
                    throttle=throttle, 
                    brake=0.0, 
                    steer=0.0
                ))
                
                # Check if getting close
                if distance < 4.0:
                    rear_collision_stage = "CLOSE"
                    print(f"[ANIMATION] Rear vehicle closing in - {distance:.1f}m")
            else:
                # Timeout - force to close stage
                rear_collision_stage = "CLOSE"
        
        elif rear_collision_stage == "CLOSE":
            # Stage 2: Final approach - check for impact
            if distance > 2.0:
                # Continue approaching
                rear_vehicle.apply_control(carla.VehicleControl(
                    throttle=0.5,
                    brake=0.0, 
                    steer=0.0
                ))
            else:
                # Impact detected!
                rear_collision_stage = "IMPACT"
                print(f"[ANIMATION] IMPACT! Rear vehicle hit ego bike at {distance:.2f}m")
                
                # FREEZE BOTH VEHICLES IMMEDIATELY
                # 1. Stop ego bike completely
                self.world.player.set_target_velocity(carla.Vector3D(0, 0, 0))
                self.world.player.apply_control(carla.VehicleControl(
                    throttle=0.0,
                    brake=1.0,
                    hand_brake=True
                ))
                print("[ANIMATION] Ego bike frozen")
                
                # 2. Stop and destroy rear vehicle
                if rear_vehicle is not None and rear_vehicle.is_alive:
                    print("[ANIMATION] Stopping rear vehicle")
                    rear_vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
                    rear_vehicle.apply_control(carla.VehicleControl(
                        throttle=0.0,
                        brake=1.0,
                        hand_brake=True
                    ))
                    print("[ANIMATION] Destroying rear vehicle")
                    rear_vehicle.destroy()
                    rear_vehicle = None
                    print("[ANIMATION] Rear vehicle destroyed successfully")
                else:
                    print("[WARNING] Rear vehicle already destroyed or None")
        
        elif rear_collision_stage == "IMPACT":
            # Both vehicles frozen - trigger fall immediately
            if elapsed > 0.1:  # Minimal delay - just 0.1 seconds
                print("\n" + "="*60)
                print("[REAR COLLISION] AUTO-FALL: Triggering fall sequence")
                print("="*60)
                
                # Stop rear collision
                rear_collision_active = False
                rear_collision_stage = "NONE"
                
                # Determine fall direction with priority
                global tilt_status, last_keyboard_direction
                
                # Priority 1: Check fall_status.txt
                current_tilt = read_tilt_status()
                print(f"[DEBUG] fall_status.txt: '{current_tilt}'")
                
                if current_tilt in ["LEFT", "RIGHT"]:
                    fall_direction = current_tilt
                    print(f"[PRIORITY 1] Using fall.txt: {fall_direction}")
                # Priority 2: Check last keyboard arrow press
                elif last_keyboard_direction in ["LEFT", "RIGHT"]:
                    fall_direction = last_keyboard_direction
                    print(f"[PRIORITY 2] Using keyboard: {fall_direction}")
                else:
                    # Priority 3: FORCE default LEFT
                    fall_direction = "LEFT"
                    print(f"[PRIORITY 3] AUTO-FALL DEFAULT: LEFT")
                
                print(f"[AUTO-FALL] Direction: {fall_direction}")
                print("="*60 + "\n")
                
                # Trigger accident immediately
                self.trigger_accident(fall_direction, "REAR_COLLISION")

    def parse_events(self, client, world, clock):
        global last_helmet_check, last_tilt_check, script_start_time, last_accident_trigger_check
        global rear_vehicle, rear_collision_active, rear_collision_start_time, rear_collision_stage
        
        current_time = time.time()
        time_since_start = current_time - script_start_time
        
        # Check proximity warning (non-accident)
        if check_warning_trigger():
            world.hud.notification("⚠️ Rear vehicle very close 🔴", seconds=1.5)
        
        # Check hotspot warning (AI/ML feature)
        is_hotspot, accident_count, distance = check_hotspot_warning()
        if is_hotspot:
            world.hud.notification(f"🤖 AI Warning: Accident-prone area ahead!  Drive carefully.", seconds=4.0)
        
        # Check if Telegram alert was sent
        try:
            if os.path.exists("telegram_status.txt"):
                with open("telegram_status.txt", "r") as f:
                    content = f.read().strip()
                if content == "SENT":
                    world.hud.notification("✅ Emergency alert sent successfully", seconds=5.0)
                    # Delete file after reading
                    try:
                        os.remove("telegram_status.txt")
                        print("[DEBUG] telegram_status.txt deleted")
                    except Exception as e:
                        print(f"[DEBUG] Failed to delete telegram_status.txt: {e}")
        except Exception as e:
            print(f"[DEBUG] Error reading telegram_status.txt: {e}")
        
        # Check hardware accident trigger
        if (not self.accident_triggered and not rear_collision_active and 
            (current_time - last_accident_trigger_check >= accident_trigger_check_interval)):
            last_accident_trigger_check = current_time
            if check_accident_trigger():
                print("\n" + "="*60)
                print("[HARDWARE TRIGGER] Accident detected by gpt-intergration.py!")
                print("[HARDWARE TRIGGER] Initiating rear collision sequence...")
                print("="*60)
                
                # Check if rear vehicle exists, respawn if needed
                if not rear_vehicle or not rear_vehicle.is_alive:
                    print("[DEBUG] Rear vehicle missing, respawning...")
                    blueprint_library = world.world.get_blueprint_library()
                    rear_blueprint = blueprint_library.find('vehicle.tesla.model3')
                    if rear_blueprint.has_attribute('color'):
                        rear_blueprint.set_attribute('color', '255,0,0')
                    
                    ego_transform = world.player.get_transform()
                    forward_vector = ego_transform.get_forward_vector()
                    rear_spawn = carla.Transform(
                        carla.Location(
                            x=ego_transform.location.x - (forward_vector.x * 10.0),
                            y=ego_transform.location.y - (forward_vector.y * 10.0),
                            z=ego_transform.location.z + 0.3
                        ),
                        ego_transform.rotation
                    )
                    rear_vehicle = world.world.try_spawn_actor(rear_blueprint, rear_spawn)
                
                if rear_vehicle:
                    ego_transform = world.player.get_transform()
                    forward_vector = ego_transform.get_forward_vector()
                    rear_position = carla.Transform(
                        carla.Location(
                            x=ego_transform.location.x - (forward_vector.x * 10.0),
                            y=ego_transform.location.y - (forward_vector.y * 10.0),
                            z=ego_transform.location.z + 0.3
                        ),
                        ego_transform.rotation
                    )
                    rear_vehicle.set_transform(rear_position)
                    rear_vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
                    
                    rear_collision_active = True
                    rear_collision_start_time = time.time()
                    rear_collision_stage = "APPROACH"
                    rear_vehicle.apply_control(carla.VehicleControl(throttle=0.5, brake=0.0, steer=0.0))
                    
                    world.hud.notification("⚠️ HARDWARE ALERT: Accident Detected! Rear Collision Triggered", seconds=4.0)
                    print("[HARDWARE TRIGGER] Rear collision sequence started")
                    print("="*60 + "\n")
        
        # Helmet detection check
        if not self.accident_triggered and (current_time - last_helmet_check >= helmet_check_interval):
            last_helmet_check = current_time
            print("\n--- Checking helmet status ---")
            check_helmet()
        
        # Tilt detection check (after startup delay)
        if (not self.accident_triggered and 
            time_since_start > startup_delay and 
            (current_time - last_tilt_check >= tilt_check_interval)):
            
            last_tilt_check = current_time
            
            status = read_tilt_status()
            
            if status in ["LEFT", "RIGHT"]:
                print(f"⚠️ Tilt detected: {status} - Triggering accident!")
                
                # Destroy Tesla if it exists
                if rear_vehicle is not None and rear_vehicle.is_alive:
                    print("[MPU] Destroying Tesla to allow fall")
                    rear_vehicle.destroy()
                    rear_vehicle = None
                
                # Stop rear collision
                rear_collision_active = False
                rear_collision_stage = "NONE"
                
                self.trigger_accident(status, "MPU")
            else:
                print(f"✓ Tilt Status: {status} (Normal)")
        
        # Startup countdown
        if time_since_start < startup_delay:
            remaining = int(startup_delay - time_since_start) + 1
            if int(time_since_start) != int(time_since_start - clock.get_time() / 1000.0):
                print(f"Starting tilt detection in {remaining} seconds...", end="\r")
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if event.key == K_ESCAPE:
                    return True
                elif event.key == K_BACKSPACE:
                    if self.accident_triggered or rear_collision_active:
                        print("Resetting vehicle - clearing all states")
                        self.accident_triggered = False
                        self.accident_side = None
                        self.keyboard_accident_mode = False
                        rear_collision_active = False
                        rear_collision_stage = "NONE"
                        if hasattr(self, 'fall_completed'):
                            delattr(self, 'fall_completed')
                        world.restart()
                elif event.key == K_h or event.key == K_SLASH:
                    world.hud.notification("WASD: Drive | 1: Toggle Helmet | 2: Rear Collision | ←→: Fall Direction | BACKSPACE: Reset", seconds=5.0)
                elif event.key == K_1:
                    # Toggle helmet status for testing
                    global helmet_ok
                    helmet_ok = not helmet_ok
                    status = "HELMET DETECTED (TEST)" if helmet_ok else "NO HELMET (TEST)"
                    world.hud.notification(status)
                    print(f"Test mode: {status}")
                elif event.key == K_LEFT:
                    global last_keyboard_direction
                    if rear_collision_active and not self.accident_triggered:
                        # During rear collision: check priority and trigger fall
                        print("\n[REAR COLLISION] LEFT arrow pressed")
                        rear_collision_active = False
                        rear_collision_stage = "NONE"
                        
                        # Priority: fall.txt -> keyboard -> default LEFT
                        current_tilt = read_tilt_status()
                        if current_tilt in ["LEFT", "RIGHT"]:
                            fall_direction = current_tilt
                            print(f"[PRIORITY 1] Using fall.txt: {fall_direction}")
                        else:
                            fall_direction = "LEFT"
                            print(f"[PRIORITY 2] Using keyboard: {fall_direction}")
                        
                        self.trigger_accident(fall_direction, "REAR_COLLISION")
                    elif not self.accident_triggered and not rear_collision_active:
                        # Normal mode: trigger accident
                        print("\n[KEYBOARD] LEFT arrow pressed")
                        last_keyboard_direction = "LEFT"
                        self.trigger_accident("LEFT", "KEYBOARD")
                elif event.key == K_RIGHT:
                    if rear_collision_active and not self.accident_triggered:
                        # During rear collision: check priority and trigger fall
                        print("\n[REAR COLLISION] RIGHT arrow pressed")
                        rear_collision_active = False
                        rear_collision_stage = "NONE"
                        
                        # Priority: fall.txt -> keyboard -> default LEFT
                        current_tilt = read_tilt_status()
                        if current_tilt in ["LEFT", "RIGHT"]:
                            fall_direction = current_tilt
                            print(f"[PRIORITY 1] Using fall.txt: {fall_direction}")
                        else:
                            fall_direction = "RIGHT"
                            print(f"[PRIORITY 2] Using keyboard: {fall_direction}")
                        
                        self.trigger_accident(fall_direction, "REAR_COLLISION")
                    elif not self.accident_triggered and not rear_collision_active:
                        # Normal mode: trigger accident
                        print("\n[KEYBOARD] RIGHT arrow pressed")
                        last_keyboard_direction = "RIGHT"
                        self.trigger_accident("RIGHT", "KEYBOARD")
                elif event.key == K_c:
                    # Switch camera view
                    world.camera_manager.switch_view()
                elif event.key == K_2 and not self.accident_triggered and not rear_collision_active:
                    # Module 3: Enhanced rear collision test
                    print("\n" + "="*60)
                    print("[KEY 2 PRESSED] INITIATING REAR COLLISION SEQUENCE")
                    print("="*60)
                    
                    # Check if rear vehicle exists, if not respawn it
                    if not rear_vehicle or not rear_vehicle.is_alive:
                        print("[DEBUG] Rear vehicle missing, respawning...")
                        
                        blueprint_library = world.world.get_blueprint_library()
                        rear_blueprint = blueprint_library.find('vehicle.tesla.model3')
                        if rear_blueprint.has_attribute('color'):
                            rear_blueprint.set_attribute('color', '255,0,0')
                        
                        ego_transform = world.player.get_transform()
                        forward_vector = ego_transform.get_forward_vector()
                        rear_spawn = carla.Transform(
                            carla.Location(
                                x=ego_transform.location.x - (forward_vector.x * 10.0),
                                y=ego_transform.location.y - (forward_vector.y * 10.0),
                                z=ego_transform.location.z + 0.3
                            ),
                            ego_transform.rotation
                        )
                        
                        rear_vehicle = world.world.try_spawn_actor(rear_blueprint, rear_spawn)
                        if rear_vehicle:
                            print("[DEBUG] Rear vehicle respawned successfully")
                        else:
                            print("[ERROR] Failed to respawn rear vehicle!")
                            continue
                    
                    if rear_vehicle:
                        # Get current ego position
                        ego_transform = world.player.get_transform()
                        forward_vector = ego_transform.get_forward_vector()
                        
                        # Calculate position exactly 10 meters behind ego
                        rear_position = carla.Transform(
                            carla.Location(
                                x=ego_transform.location.x - (forward_vector.x * 10.0),
                                y=ego_transform.location.y - (forward_vector.y * 10.0),
                                z=ego_transform.location.z + 0.3
                            ),
                            ego_transform.rotation  # Face same direction as ego
                        )
                        
                        # Teleport rear vehicle to position
                        rear_vehicle.set_transform(rear_position)
                        
                        # Reset rear vehicle velocity
                        rear_vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
                        
                        print(f"[DEBUG] Rear vehicle repositioned at 10m behind ego")
                        print(f"[DEBUG] Starting approach sequence...")
                        print(f"[DEBUG] Current last_keyboard_direction: {last_keyboard_direction}")
                        
                        # Start collision sequence
                        rear_collision_active = True
                        rear_collision_start_time = time.time()
                        rear_collision_stage = "APPROACH"
                        
                        # Initial acceleration
                        rear_vehicle.apply_control(carla.VehicleControl(
                            throttle=0.5, 
                            brake=0.0, 
                            steer=0.0
                        ))
                        
                        world.hud.notification("⚠️ Accident Prevention Alarm: Vehicles are too close from behind", seconds=4.0)
                        print("[INFO] Rear collision will trigger fall in ~2 seconds")
                        print("="*60 + "\n")
                    else:
                        print("[ERROR] Rear vehicle not found! Press BACKSPACE to reset.")
        
        # Apply control based on state priority
        if rear_collision_active:
            self.update_rear_collision()
            # Allow ego to continue driving during collision approach
            if not self.accident_triggered:
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                world.player.apply_control(self._control)
        elif self.accident_triggered:
            self.update_accident_physics()
        else:
            self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
            world.player.apply_control(self._control)
        
        return False

    def _parse_vehicle_keys(self, keys, milliseconds):
        global helmet_ok
        
        # Smooth throttle control with helmet-based limiting
        if keys[K_UP] or keys[K_w]:
            throttle_increment = 0.01
            self._control.throttle = min(self._control.throttle + throttle_increment, 1.0)
        else:
            # Gradual throttle decrease for smoother control
            self._control.throttle = max(self._control.throttle - 0.005, 0.0)
        
        # Apply helmet-based speed limiting
        if helmet_ok:
            # With helmet: allow up to 80% throttle (~60 km/h)
            max_throttle = 0.8
        else:
            # No helmet: limit to 35% throttle (~30 km/h)
            max_throttle = 0.35
        
        self._control.throttle = min(self._control.throttle, max_throttle)

        # Brake control
        if keys[K_DOWN] or keys[K_s]:
            self._control.brake = min(self._control.brake + 0.1, 1.0)
            self._control.throttle = 0.0
        else:
            self._control.brake = max(self._control.brake - 0.1, 0.0)

        # Smooth steering control
        steer_increment = 3e-4 * milliseconds  # Reduced for smoother steering
        if keys[K_LEFT] or keys[K_a]:
            if self._steer_cache > 0:
                self._steer_cache = 0
            else:
                self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            if self._steer_cache < 0:
                self._steer_cache = 0
            else:
                self._steer_cache += steer_increment
        else:
            # Gradual return to center
            if abs(self._steer_cache) > 0.01:
                self._steer_cache *= 0.95
            else:
                self._steer_cache = 0.0
        
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 2)
        
        # Hand brake
        self._control.hand_brake = keys[K_SPACE]
        
        # Reverse
        if keys[K_q]:
            self._control.gear = 1 if self._control.reverse else -1
        self._control.reverse = self._control.gear < 0

# ================= HUD Class =================
class HUD(object):
    def __init__(self, width, height):
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self._font_mono = pygame.font.Font(pygame.font.get_default_font(), 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        
        v = world.player.get_velocity()
        c = world.player.get_control()
        speed_kmh = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
        
        # Combined status display
        helmet_status = "DETECTED" if helmet_ok else "NOT DETECTED"
        helmet_confirm = "ACTIVE" if model is not None else "DISABLED"
        tilt_display = tilt_status if tilt_status != "NONE" else "NORMAL"
        
        # Show collision stage if active
        collision_status = rear_collision_stage if rear_collision_active else "READY"
        
        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Speed:   % 15.0f km/h' % speed_kmh,
            f'Helmet:  {helmet_status} ({helmet_confirm})',
            f'Tilt:    {tilt_display}',
            f'Rear:    {collision_status}',
            '',
            ('Throttle:', c.throttle, 0.0, 1.0),
            ('Steer:', c.steer, -1.0, 1.0),
            ('Brake:', c.brake, 0.0, 1.0),
        ]

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def render(self, display):
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((100, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((100, v_offset + 8), (106, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        rect = pygame.Rect((100, v_offset + 8), (f * 106, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        
        self._notifications.render(display)

class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)

# ================= Sensor Classes =================
class CollisionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.hud = hud
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=parent_actor)

class CameraManager(object):
    def __init__(self, parent_actor, hud, gamma_correction):
        self.sensor = None
        self.surface = None
        self.hud = hud
        self.current_view = 0  # 0: Third person, 1: First person, 2: Side view, 3: Top view
        self.view_names = ["Third Person", "First Person", "Side View", "Top View"]
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(hud.dim[0]))
        bp.set_attribute('image_size_y', str(hud.dim[1]))
        
        # Start with third person view
        self.sensor = world.spawn_actor(
            bp,
            carla.Transform(carla.Location(x=-5.5, z=2.5), carla.Rotation(pitch=8.0)),
            attach_to=parent_actor
        )
        
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
    
    def switch_view(self):
        """Switch between different camera views without affecting vehicle state"""
        self.current_view = (self.current_view + 1) % 4
        
        # Destroy current sensor
        if self.sensor:
            self.sensor.destroy()
        
        # Get parent actor (the bike)
        parent_actor = self.hud.world.player
        
        if not parent_actor:
            return
        
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find('sensor.camera.rgb')
        bp.set_attribute('image_size_x', str(self.hud.dim[0]))
        bp.set_attribute('image_size_y', str(self.hud.dim[1]))
        
        # Define camera positions for different views
        if self.current_view == 0:  # Third person
            transform = carla.Transform(carla.Location(x=-5.5, z=2.5), carla.Rotation(pitch=8.0))
        elif self.current_view == 1:  # First person
            transform = carla.Transform(carla.Location(x=0.8, z=1.7), carla.Rotation(pitch=0.0))
        elif self.current_view == 2:  # Side view
            transform = carla.Transform(carla.Location(x=0.0, y=-8.0, z=3.0), carla.Rotation(pitch=10.0, yaw=90.0))
        else:  # Top view
            transform = carla.Transform(carla.Location(x=0.0, z=15.0), carla.Rotation(pitch=-90.0))
        
        # Spawn new sensor
        self.sensor = world.spawn_actor(bp, transform, attach_to=parent_actor)
        
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        
        # Notify user of view change
        self.hud.notification(f"Camera: {self.view_names[self.current_view]}", seconds=2.0)

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        image.convert(cc.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

# ================= Main Game Loop =================
def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None

    try:
        global script_start_time
        script_start_time = time.time()
        
        client = carla.Client(args.host, args.port)
        client.set_timeout(20.0)  # Increased timeout
        
        # Try to connect with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                world_obj = client.get_world()
                print("✓ Connected to CARLA server")
                break
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    raise Exception(f"Failed to connect after {max_retries} attempts")

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        
        pygame.display.set_caption('CARLA - Enhanced Collision Animation System')

        hud = HUD(args.width, args.height)
        world = World(world_obj, hud, args)
        controller = CombinedControl(world)

        # Initialize detection systems
        helmet_init = init_helmet_detection()
        read_tilt_status()
        
        print(f"Helmet Detection: {'✓ Active' if helmet_init else '✗ Disabled'}")
        print(f"Initial tilt status: {tilt_status}")
        print(f"Tilt detection starts in {startup_delay} seconds...")
        print("ENHANCED ANIMATION SYSTEM READY")
        print("Press '2' for dramatic rear collision sequence!\n")

        clock = pygame.time.Clock()
        
        while True:
            clock.tick(30)
            if controller.parse_events(client, world, clock):
                return
            world.tick(clock)
            world.render(display)
            pygame.display.flip()

    finally:
        if world is not None:
            world.destroy()
        if cap is not None:
            cap.release()
        pygame.quit()

def main():
    argparser = argparse.ArgumentParser(description='CARLA Enhanced Collision Animation System')
    argparser.add_argument('--host', default='127.0.0.1', help='IP of the host server')
    argparser.add_argument('-p', '--port', default=2000, type=int, help='TCP port to listen to')
    argparser.add_argument('--res', default='1280x720', help='window resolution')
    argparser.add_argument('--rolename', default='hero', help='actor role name')
    argparser.add_argument('--gamma', default=2.2, type=float, help='Gamma correction')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    print("\n" + "="*70)
    print("CARLA ENHANCED COLLISION ANIMATION SYSTEM")
    print("="*70)
    print("\nNEW FEATURES:")
    print("  ✓ Multi-stage rear collision animation")
    print("  ✓ Realistic impact physics with impulse forces")
    print("  ✓ Smooth easing functions for natural motion")
    print("  ✓ Progressive tilting and fall sequence")
    print("  ✓ Enhanced visual feedback and timing")
    print("\nMODULES:")
    print("  Module 1: Helmet Detection (YOLO + Laptop Webcam)")
    print("  Module 2: Tilt-based Accident Simulation")
    print("  Module 3: ENHANCED Rear Collision with Cinematic Animation")
    print("\nCONTROLS:")
    print("  W/S or ↑/↓  : Throttle / Brake")
    print("  A/D         : Steer Left / Right")
    print("  ← →         : Simulate Left/Right Accident")
    print("  1           : Toggle Helmet Detection")
    print("  2           : ENHANCED Rear Collision (Cinematic!)")
    print("  SPACE       : Handbrake")
    print("  Q           : Toggle Reverse")
    print("  BACKSPACE   : Reset after accident")
    print("  H or ?      : Show help")
    print("  ESC         : Quit")
    print("\nREQUIRED FILES:")
    print("  - best.pt (YOLO helmet model)")
    print("  - fall_status.txt (tilt sensor data)")
    print("="*70 + "\n")

    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    except Exception as e:
        print(f'Error: {e}')
        print('Make sure CARLA server is running on 127.0.0.1:2000')

if __name__ == '__main__':
    main()