#!/usr/bin/env python3
import gym
from gym import wrappers
import gym_gazebo
import time
import numpy
import random
import time

import qlearn
import liveplot

import os.path
from os import path

import inspect

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno


def render():
    render_skip = 0 #Skip first X episodes.
    render_interval = 50 #Show render Every Y episodes.
    render_episodes = 10 #Show Z episodes every rendering.

    if (x%render_interval == 0) and (x != 0) and (x > render_skip):
        env.render()
    elif ((x-render_episodes)%render_interval == 0) and (x != 0) and (x > render_skip) and (render_episodes < x):
        env.render(close=True)


if __name__ == '__main__':

    # Setup environment
    env = gym.make('GazeboCartPole-v0')

    # NEW START ----------------

    # Print action space size
    print(f"Action space size: {env.action_space.n}")
    
    # Print observation space
    observation = env.reset()
    print(f"Observation space: {observation}")
    print(f"Shape of observation space: {numpy.shape(observation)}")

    # NEW END ------------------S

    outdir = '/tmp/gazebo_gym_experiments'
    env = gym.wrappers.Monitor(env, outdir, force=True)
    plotter = liveplot.LivePlot(outdir)

    last_time_steps = numpy.ndarray(0)

    # Setup qlearning
    qlearn = qlearn.QLearn(actions=range(env.action_space.n),
                           alpha=0.2, gamma=0.8, epsilon=0)

    initial_epsilon = qlearn.epsilon

    epsilon_discount = 0.999956

    # Load parameters, move file before running if not wanted
    from datetime import datetime
    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d-%m-%Y=%H-%M-%S")
    print("**************date and time =", dt_string)
    filename = dt_string + '.pkl'
    filename = "15-08-2019=16-28-09.pkl"
    if path.exists(filename):
        #qlearn.loadParams(filename)
        print("**************Loading params from {}".format(filename))
    else:
        print("**************{} not found. Starting fresh.".format(filename))

    # Setup for looping
    start_time = time.time()
    total_episodes = 100000
    highest_reward = 0

    for x in range(total_episodes):
        # Reset for episode
        done = False
        cumulated_reward = 0  # Should going forward give more reward then L/R?
        observation = env.reset()

        # Decrease chance of random action
        if qlearn.epsilon > 0.05:
            qlearn.epsilon *= epsilon_discount

        # render() #defined above, not env.render()

        state = ''.join(map(str, observation))
        qlearn.num_times_learn = 0
        qlearn.num_times_seen_before = 0

        # To change max episode steps, go to gym_gazebo/__init__.py
        i = -1
        while True:
            i += 1

            # Pick an action based on the current state
            action = qlearn.chooseAction(state)

            # Execute the action and get feedback
            observation, reward, done, info = env.step(action)
            cumulated_reward += reward

            if highest_reward < cumulated_reward:
                highest_reward = cumulated_reward

            nextState = ''.join(map(str, observation))

            qlearn.learn(state, action, reward, nextState)
            angle = observation[2]
            angular_v = observation[3]
            if (state, 0) in qlearn.q:
                reward0 = qlearn.q[(state, 0)]
            else:
                reward0 = 0
            if (state, 1) in qlearn.q:
                reward1 = qlearn.q[(state, 1)]
            else:
                reward1 = 1
            #print("Angle: {}\nAngular: {}\nReward for forward: {}.\nReward for backward: {}\n******".format(angle, angular_v, reward1, reward0))

            env._flush(force=True)

            if not(done):
                state = nextState
            else:
                last_time_steps = numpy.append(last_time_steps, [int(i + 1)])
                break
        print("Amount of state action pairs seen before: {}/{}".format(qlearn.num_times_seen_before, qlearn.num_times_learn))

        # Update plot and save params every 100 episodes
        if x%100==0:
            plotter.plot(env)
            # qlearn.saveParams(filename)
            print("Saving params to {}".format(filename))

        m, s = divmod(int(time.time() - start_time), 60)
        h, m = divmod(m, 60)
        print ("EP: "+str(x+1)+" - [alpha: "+str(round(qlearn.alpha,2))+" - gamma: "+str(round(qlearn.gamma,2))+" - epsilon: "+str(round(qlearn.epsilon,2))+"] - Reward: "+str(cumulated_reward)+"     Time: %d:%02d:%02d" % (h, m, s))

    #Github table content
    print ("\n|"+str(total_episodes)+"|"+str(qlearn.alpha)+"|"+str(qlearn.gamma)+"|"+str(initial_epsilon)+"*"+str(epsilon_discount)+"|"+str(highest_reward)+"| PICTURE |")

    l = last_time_steps.tolist()
    l.sort()

    #print("Parameters: a="+str)
    print("Overall score: {:0.2f}".format(last_time_steps.mean()))
    print("Best 100 score: {:0.2f}".format(reduce(lambda x, y: x + y, l[-100:]) / len(l[-100:])))
    env.close()
