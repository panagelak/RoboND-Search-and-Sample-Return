import numpy as np
import random

# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!


    # Example:
    # Check if we have vision data to make decisions with  

    if Rover.nav_angles is not None:

        # save the initial position in the Rover.start_pos variable

        if Rover.total_time < 0.04:
            print(Rover.pos)
            Rover.start_pos = Rover.pos

        # checks if all samples are collected
        # if so it will stop when it is close to the start location

        if Rover.samples_collected == 6:
            print("all samples collected go back to base")
            dist = (((Rover.pos[0] - Rover.start_pos[0])**2) + \
            ((Rover.pos[1] - Rover.start_pos[1])**2)**0.5)
            if dist < 10:
                print("ALL SAMPLES COLLECTED AND NEAR START LOCATION SUCCESS")
                Rover.brake = Rover.brake_set
                Rover.throttle = 0
                Rover.steer = 0

                return Rover

        # if we see navigable terain ahead but we are not moving
        # this means we are stuck
        # To avoid getting stuck in the beggining where this conditions
        # are met we have the stuck_counter variable

        if Rover.vel < 0.2 and Rover.mode == "forward":
            Rover.stuck_counter += 1
            if Rover.stuck_counter > 120:
                Rover.stuck_counter = 0
                Rover.mode = "stuck"
                return Rover
              

        # if we steer to the left with big steering angle for some time
        # we are probably looping we change the mode to "looping"
        # so we can break from this state

        if Rover.steer > 10 and Rover.vel > 0.6:
            Rover.loop_counter +=1
            if Rover.loop_counter == 600:
                Rover.loop_counter = 0
                Rover.mode = "loop"
                return Rover
        else:
            Rover.loop_counter = 0


        # if we detect that we are looping
        # we will brake and after head straight ahead
        # this should get us out of a loop

        if Rover.mode == "loop":
            Rover.loop_counter += 1
            if Rover.loop_counter < 10:
                Rover.brake = Rover.brake_set
            elif Rover.loop_counter >= 10 and Rover.loop_counter < 250:
                Rover.throttle = Rover.throttle_set
                Rover.steer = 0
                Rover.brake = 0
            else:
                Rover.loop_counter = 0
                Rover.mode = "forward"

        # if we detect a rock from the perception step we change the mode
        # to go_to_rock then we brake and we are heading straight to the rock
        # if we are in grabbing distance we will brake and grab it
        # if we get stuck along the way we will try to steer to the right for
        # a short amount of time so we wont lose shight of the rock

        elif Rover.mode == "go_to_rock":


            Rover.go_to_rock_counter += 1

            if Rover.go_to_rock_counter < 10: 

                Rover.brake = Rover.brake_set

            elif Rover.go_to_rock_counter >= 10 and Rover.go_to_rock_counter < 300:


                if Rover.near_sample == 1:
                    Rover.go_to_rock_counter = 0


                    Rover.throttle = 0 
                    Rover.brake = Rover.brake_set

                    if Rover.vel == 0:
                        Rover.send_pickup = True
                        Rover.go_to_rock_counter = 0
                        Rover.mode = "stop"
                        return Rover
                else:
                    
                    Rover.brake = 0
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi ), -15, 15)
                    Rover.throttle = Rover.throttle_set
                    
            elif Rover.go_to_rock_counter >= 300 and Rover.go_to_rock_counter < 320:
                Rover.steer = -15
                Rover.brake = 0
                Rover.throttle = 0
            else:
                Rover.go_to_rock_counter = 0
                Rover.brake = 0
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi ), -15, 15)
                Rover.throttle = Rover.throttle_set
                Rover.mode = "forward"
            
        # if we are stuck
        # we will brake then steer to the right
        # and head straight ahead so we get unstuck

        elif Rover.mode == 'stuck':
            Rover.stuck_counter +=1
            if Rover.stuck_counter < 20:

                Rover.throttle = 0
                Rover.steer = 0
                Rover.brake = Rover.brake_set

            elif Rover.stuck_counter >= 20 and Rover.stuck_counter < 50:
                Rover.brake = 0
                Rover.steer = -15

            elif Rover.stuck_counter >= 50 and Rover.stuck_counter < 80:
                Rover.throttle = Rover.throttle_set

            else:
                Rover.stuck_counter = 0
                Rover.mode = 'forward'

        
        
        elif Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            

            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting

                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0

                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15

                # we use a big offset so we realy get stuck in the left wall

                offset = 16
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi + offset), -15, 15)
                
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
                 

            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        if Rover.picking_up == 1:
            if Rover.send_pickup == False:
                Rover.send_pickup = True
                Rover.samples_collected += 1
            return Rover
        else:
            Rover.send_pickup = False
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

