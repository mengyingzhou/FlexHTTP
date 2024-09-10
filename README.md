# 1. FlexHTTP
FlexHTTP is an intelligent and scalable HTTP version selection system. FlexHTTP embeds a supervised machine learning-based classifier to select the appropriate HTTP version according to network conditions and page structures. FlexHTTP adopts a set of distributed agent servers to ensure scalability and keep the classifier up-to-date with the dynamic network. 


> Mengying Zhou, Zheng Li, Qiang Duan, Shihan Lin, Yupeng Li, Xin Wang, and Yang Chen. "FlexHTTP: Making HTTP Protocol Intelligent and Scalable". Submitted to IEEE Transactions on Network and Service Management

> A preliminary version of this paper has been published in EuroMLsys'22. [Link](https://doi.org/10.1145/3517207.3526972)


For any questions, please post an issue.


# 2. Create Machines on Emulab
We use [Emulab](https://www.emulab.net/portal/frontpage.php), a representative network emulation testbed to testbed to conduct a proof-of-concept evaluation of FlexHTTP. Emulab provides a controllable experimental environment to define network topologies, network parameters, machine configuration, etc.

Emulab provides the Python API to create the network topo. You can click `Experiments` -> `Create Experiment Profile` in the user Dashboard. Then upload [init/CreateEmulabVM.py](init/CreateEmulabVM.py). This script contains the deployment of `Sever`, `Client`, and `Agent`. The `args_list` variable is the configured network conditions (corresponding to RTT, loss rate, and bandwidth). Once you upload the profile, you can click the `instantiate` in this profile page to complete the deployment of the machines. 


# 3. Dependencies Installation 
**This initiation script will change the environment setting. We don't recommend trying our FlexHTTP prototype on your own personal PC.**

We need to add some environment variables. We recommend switching to the `bash` shell and then executing the following commands under the bash shell.
```shell
bash cli.sh install
```
Although Emulab can sync data in your home folder, you still should run this command on each VM.

If you don't use the Python script [init/CreateEmulabVM.py](init/CreateEmulabVM.py) to create the VMs on Emulab, you should change the environment variables in the [init/install.sh](init/install.sh) file. The default FLEXHTTP folder is located in the home folder. The SERVER IP is `10.10.0.1`, and the AGENTIP is `10.20.0.3`.
```
export FLEXHTTP=<FlexHTTP folder path>
export SERVERIP=<server ip for the client>
export AGENTIP=<agent ip for the client>
```
We write the environment variables with bash shell. If you use other terminal shells, you should add these variables into its shell script (e.g., .zshrc for zsh shell). 

# 4. How to run

## 4.1. Machine Types
- server: the server hosting the corresponding crawled Alexa Top250 webpage. H2 and H3 services are opened at 10001 and 10002 ports, respectively.
- agent: the middleware of FlexHTTP 
- client: the user client


## 4.2. Server
```
bash cli.sh server
```

We don't provide the crawled Alex Top240 web pages since it's huge. But you still can use the test alexa_top240 folder to verify the server function, and click [here](https://doi.org/10.5281/zenodo.6378149) to download the full pages.

After downloading all pages, you should
```
cp -r alexa_top240 ${FLEXHTTP}/server
```

In the Caddy configuration file, we use `example.com` as the test domain. If you want to test FlexHTTP with your own domain, you should apply for the validation SSL certification from trusted CAs or make Chrome trust your own-made SSL certification with [mkcert](https://github.com/FiloSottile/mkcert).



## 4.3. Agent
```
bash cli.sh agent
```

We have pre-set the trained global model [myUtil/ai_model/global_model.pkl](myUtil/ai_model/global_model.pkl) with 556,800 experiment configurations in various network conditions.

## 4.4. Client
```
bash cli.sh client-init
```
Please run client-init before the client start


```
bash cli.sh client
```


# 5. Stop Experiment 
```
bash cli.sh stop
```

# 6. Experiment results
You can find the results in `HOME/exp_results`, where `HOME` is the user's home folder path.
- `FlexHTTP_results`: The performance recorded for each test trace.
- `json_results`: If you are using Lighthouse to capture performances, the raw Lighthouse result files will be saved here.
- `har_results`: If you use HAR to capture PLT, the raw HAR file will be saved here.

`HOME/log` records debug log content.