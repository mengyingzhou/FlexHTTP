#!/usr/bin/env bash
case $1 in
    install)
        echo "install"
        cd "init"
        bash "install.sh"
        echo "install done"
        ;;
    server)
        echo "server"
        bash "${FLEXHTTP}/server/serverStart.sh"
        echo "server running"
        ;;
    agent)
        echo "agent"
        bash "${FLEXHTTP}/agent/agentStart.sh"
        echo "agent running"
        ;;
    client-init)
        # WARNING: please run client-init before client start
        bash "${FLEXHTTP}/client/scripts/clientInit.sh"
        ;;
    client)
        # bash "${FLEXHTTP}/client/scripts/clientStartAgent.sh" ${arg1} ${arg2} ${arg3} 
        # !!! the all three args have the default setting, you don't need to specify them
        # ${arg1}: The network condition of configuration, <RTT>-<loss rate>-<bandwidth>.
        # For Emulab test, we can obtain the information from the client's hostname environment
        # ${arg2}: experiment name. If you don't provide a specific name, we will use the 
        # current time as the experiment name.
        # ${arg3}: whether need to per-train the initial model, default is False
        bash "${FLEXHTTP}/client/scripts/clientStart.sh"
        ;;
    stop)
        bash "${FLEXHTTP}/server/serverStop.sh"
        bash "${FLEXHTTP}/client/global_pool/agentStop.sh"
        bash "${FLEXHTTP}/client/scripts/clientStop.sh"
        if [ -f "${FLEXHTTP}/client/band.json" ]; then
            rm "${FLEXHTTP}/client/band.json"
        fi
        if [ -f "${FLEXHTTP}/client/ping.json" ]; then
            rm "${FLEXHTTP}/client/ping.json"
        fi
        ;;
    *)
        echo "choose argument from: install agent server client-init client"
        ;;
esac
