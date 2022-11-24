# Overview
This project acts as the visualization controller. It is a Node.js server that makes use of WebSockets to synchronize actions across multiple clients. The logical flow is as follows: clients submit a `join` message to the room they wish to join. This room is a string specifying different instances of visualizations to connect to. Currently, the client automatically connects to a room called `default`. If the room the client connects to already exists, the client will be synch'd with the current state of the visualization. Otherwise, the room will be created and initialized as an empty visualization.

# Installation
There are two different installation strategies: Using Docker or following more traditional installation strategies. Docker lets you get a new machine up and running within minutes, but it can require rebuilding Docker images to see changes reflected in one of our UIs, depending on what you're changing and how you're running your Docker containers.

Regardless of which method you choose, you first need to **clone this repository (and the CosmosD3 and Nebula-Pipeline repositories)** onto your local machine. (Be sure you have git installed, and install it [here](https://git-scm.com/downloads) if you don't have it already. You don't need the GUI; the command line tool should be sufficient and will likely cause you fewer issues with this project.) When initialing cloning from git, be sure to either run `git clone --recurse-submodules` (recommended), or `git submodule init` followed by `git submodule update` to pull in the CosmosD3 and Nebula-Pipeline submodules.

## Docker Installation
Make sure you have a version of **Docker** installed from [the official website](https://docs.docker.com/install/) (look to the menu on the left to get a version installed for your OS, making sure to double check your system requirements and installing the older Docker Toolbox if necessary, and note that **Docker Desktop is not compatible with VirtualBox**). Just about any version of Docker should do; we are just using *images* and *containers*, not *services*, *networks*, or any other Docker features.

Before you can do much with Docker, you may have to get a *Docker daemon* running. The steps you take depend on your OS and whether you are using Docker Desktop or Docker Toolbox. As you go through these steps, pay attention to your terminal output as there may be additional commands listed for you to run in order to complete this setup. If you run into issues, please read [this page](https://docs.docker.com/machine/get-started/) for more guidance.

* **Docker Toolbox on Mac OS**:
To get the default daemon running, these commands can be helpful (when in doubt, you can run all 3 in this order; more information is available [here](https://stackoverflow.com/questions/21871479/docker-cant-connect-to-docker-daemon)):
    * `docker-machine start` # Start virtual machine for docker
    * `docker-machine env`  # Get environment variables
    * `eval "$(docker-machine env default)"` # Set environment variables

* **Docker Desktop on Mac OS**:
You likely will not have to do any additional setup; Docker Desktop should be able to run straight from the installation.

* **Docker Desktop on Windows**:
Follow the instructions listed [here](https://docs.docker.com/machine/drivers/hyper-v/) to get Hyper-V running. Note that Step 2 is not optional if you haven’t done it before. **Be sure that you are running PowerShell as administrator as you use Docker.** At the end, you will likely need to run `docker-machine create`.

* **All OS's**:
Once you have done any preliminary setup steps, you may have to run `docker-machine start` to actually start the default machine. Addtionally, if the docker machine ever stops, you will not be able to run any containers. If this happens, simply use this command again (along with any others that may come up in your terminal) to start the default machine.



Next, **`cd` into the directory** where your cloned repository lives. You should see a Dockerfile there, which specifies what a Docker image should look like (including all dependencies) and what it should do on startup (as defined by CMD). To **build your Docker image**, run

`docker build -t imageName .`

For example, I call my image `nebulaserver`. The `.` simply specifies your current directory as the location of the desired Dockerfile is located. Make sure you don't have any errors or warnings in building your image (aside from deprecation warnings; these are to be expected). Assuming everything went smoothly, you now have a Docker image ready.

*Developer Tip:* If you have already used Docker before and are trying to create a new, updated image (based on changes to the Docker file), use the `--no-cache` flag to force Docker to completely rebuild the image from scratch (i.e., without any cached information): `docker build --no-cache -t imageName .` This may take longer for Docker to create the image.

Your docker image is not yet running. To run it, you need to use `docker run -p hostPort:containerPort imageName`. This **runs the given image (e.g., `nebulaserver`) within a container**, where the image is running the given application on `containerPort` (which for us is typically `4040`, as defined in app.js; this port is then "exposed" to the host machine with the `EXPOSE` command in the Dockerfile). This container port is then mapped to the given host port, which can be any unused port you want it to be (e.g, `80`). Your app should now be ready for you to use. You will see in your console printout from within your container print to the terminal window that you launched your container in. Note, however, that your container will be unresponsive to any keyboard input from this terminal window (including the typical `CTRL+C` to stop the Node.js server).

*Note:* I recommend you run a longer command to start your container... See below for details:

**Recommended Command for Mac users**:

`docker run -v $(pwd)/CosmosD3:/www/CosmosD3/ -v $(pwd)/Nebula-Pipeline:/www/Nebula-Pipeline/ -p 4040:4040 --name nebula_runner1  nebulaserver`

**Recommended Command for Windows users**:

`docker run -v $(pwd)\CosmosD3:/www/CosmosD3/ -v $(pwd)\Nebula-Pipeline:/www/Nebula-Pipeline/ -p 4040:4040 --name nebula_runner1  nebulaserver`


Lastly, to figure out how to **connect to your app**, you need to know which IP address your Docker container is running on. Docker containers run on the IP address associated with the daemon that it's being run on. To figure out what that IP address is, first try

`docker-machine ip default`

in a different terminal window (which will tell you the IP address associated with your default daemon; if you've specified a different one, replace `default` with the name of your other daemon). For some machines, this may be `127.0.0.1` (i.e., localhost), whereas others (particularly those that use the older Docker Toolbox), this may be `192.168.99.100`. For example, for a machine running Docker Toolbox that has mapped the host port `4000` to the container's port, you would access Andromeda through the URL `192.168.99.100:4000/cosmos/andromeda.html`.

If you are having difficulties connecting to your app, you may need to instead find the proper IP address by running

`ipconfig`

This command will print network information into your terminal. Look for a line that reads, "Ethernet adapter vEthernet (DockerNAT)," and use the IPv4 address listed there (e.g., 10.0.75.1). For more information or additional troubleshooting, you can start by looking at [this StackOverflow page](https://stackoverflow.com/questions/40746453/how-to-connect-to-docker-host-from-container-on-windows-10-docker-for-windows).



### Other Useful Docker Commands

#### Additional Options for Running Containers
As previously mentioned, you can add more to your `docker run` command to make it do even more powerful things for you. Here's a few of available options:
* `--name containerName` : You specify the container's name yourself as `containerName`. Otherwise, a randomly generated name will be assigned to it. Specifying the name yourself is useful since it means you will know what your container's name is, making it easier to stop or restart the container later (as described below). In the example above, I use `--name nebula_runner1`. Note that the specified `containerName` must be unique. (See below to remove existing containers, which may have the same name as the name you're trying to use.)
* `-v /full/path/to/hostDir:/full/path/to/container/dir` : The specified directory in your host machine will be mounted to the specified directory in your container. Since your container is running a static image, this means that traditionally you would have to rebuild your image to see any changes reflected in how your container operates. By instead mounting a host directory, you can make changes to things in your host machine and see those changes instantly reflected in your container. Note that this doesn't change your image, however, so rebuilding your image regularly is still a good idea. Additionally, don't try to mount the entire Nebula directory as the node_modules directory contained within will conflict with the node_modules directory that your container tries to make to let the Node.js server run properly. The result will be that the process will crash, causing your container to automatically stop running. (It's not very useful to mount the Node.js files anyways since the container begins running (with the `npm start` command), and then the mounting takes place, meaning changes to files like nebuja.js won't be visible unless you resart the npm process. But if that process stops, then the container stops, so you might as well rebuild the image and start a new container.) In the example above, I mount both the Nebula-Pipeline and CosmosD3 directories from my host machine to the container to let me make and see changes easily.
   * **Note for Windows users**: Windows users should use '\' instead of '/' when defining the file paths on your local machine, but keep '/' for the host machine. See the recommended command above for an example.
* `-d` : You can run your Docker container run in a detached state. According to the official [docs](https://docs.docker.com/engine/reference/run/#detached--d), "by design, containers started in detached mode exit when the root process used to run the container exits." Therefore, using this detached state may be useful if you want your Docker container to continue after the main process (dictated by CMD) terminates. However, it does mean that the container's output will no longer be printed out to your host's terminal.

#### Stopping, Starting, Attaching, Seeing Logs, and Removing Containers
To stop a container, you need the container's name. If you forgot it or didn't specify a name, you can get the information by running `docker ps`. Then, run `docker stop containerName`. Following my examples above, I would run `docker stop nebula_runner1`.

Note, however, that this doesn't completely remove the container; it has merely stopped running. Using `docker ps -a` will show you all containers, including those that aren't currently running. What this lets you do is run `docker start containerName` to restart the same, previously defined container (including all the mounting settings you used when you initially ran the container). However, notice that you are starting the container in a detached state. To attach to a container that you are detached to (either by starting a pre-existing container or using the `-d` flag mentioned above, you can use the command `docker attach containerName`. Attaching to a container will allow you to start seeing any *new* output in that container, but you will not be able to see any previous output in that container. To see old logs, use the `docker log containerName`. Using the `-f` flag for this command will allow you to see new logs as they happen as well.

Have images or containers you want to get rid of? One of these commands may help you (with more information available [here](https://linuxize.com/post/how-to-remove-docker-images-containers-volumes-and-networks/):
* `docker container rm containerID` : Removes the container with the specified containerID, which is either the container's ID number or its name (which can both be obtained using `docker ps -a`)
* `docker container prune` : Removes all stopped containers
* `docker image prune` : Removes all dangling images
* `docker system prune` : Removes all stopped containers, all dangling images, and all unused networks

#### Executing a Command Within a Container
If you want to execute a command within a container, use `docker exec -it containerID /container/path/to/bash`. This will allow you to execute whatever commands you want from within the container with the specified ID number (which you can obtain using `docker ps`). Type `exit` when you are ready to return to your host machine (just like when using ssh). For our project, the path to bash is simply `/bin/bash`.

## Traditional Installation
Some dependencies must be installed differently for each platform. These instructions focus on getting the NPM server working as well as the pipeline code contained in the Nebula-Pipeline directory since the visualizations themselves (contained in the Nebula-UIs directory) do not need any additional setup beyond this.

The code in Nebula-Pipeline performs all the back end data processing for the visualizations. Each pipeline instantiation executes as a single Python script and is made up of three main pieces: a data controller, a series of models, and a connector. The data controller handles loading and accessing whatever data is to be visualized. The models control how the data is processed and sent to the client, as well as how the client's interactions change these models. Finally, the connector mediates connections to the visualization directly or to a visualization controller such as the Node.js server.

### UPDATES AS OF 11/23/2022
Instructions for installation in **Ubuntu 20.04** can be found in `LocalInstall.md`. You can run each command in order to install all of the proper dependencies. You also can run the script `LocalInstall.sh` to automate the installation process.

### Installing Python

For all platforms, **Python 3** must be installed for Nebula-Pipeline to work. This install should come with **pip3**, the Python package manager. If you can run pip from the command line, you are ready to proceed.

#### Python Compatibility Issues

Previous resarchers on this project have tried to use [Anaconda](https://www.continuum.io/downloads) as a Python distribution with preinstalled packages. However, do note that using Anaconda may cause issues with installing and running this project correctly, especially if Anaconda is installed after this project.

### Installing Java

**Java** must also be installed for the project to run correctly. It can be installed from [here](https://www.java.com/en/download/).

### Installing Node.js

Install **Node.js** version 18.X [here](https://nodejs.org/dist/latest-v18.x/).

### OS-Specific Instructions

#### Windows

*Developer Tip: Any LTS version at or below 4.4.7 will not work correctly.  As of this writing, the newest version is 8.11.1 LTS, with which the rest of the instructions should work fine. To fix this issue, you must run `npm install -g npm`, and then go into your `~\AppData\Roaming\npm\node_modules\npm` directory and run the command `npm install node-gyp@3.4.0`. With this, the remaining instructions should work. Any LTS Node.js version after 4.4.7 should not need to the aforementioned steps.

Install the **Visual C++ Build Tools**, found [here](http://landinghub.visualstudio.com/visual-cpp-build-tools). Then tell the Node package manager to use this version by running:

``npm config set msvs_version 2015``

Finally, for the Nebula-Pipeline to work, the Python 2.7 packages **numpy and scipy** must be installed before running the setup below. If you already have the traditional Python distribution installed, the best way to install these packages is by downloading them from the site [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/). Download the files `numpy-1.13.1+mkl-cp27-cp27m-win_amd64.whl` and `scipy-1.0.1-cp27-cp27m-win_amd64.whl` (or the 32-bit version if that's the Python version you're running), and run the following commands in the directory these files are in:

``pip install numpy-1.13.1+mkl-cp27-cp27m-win_amd64.whl``

``pip install scipy-1.0.1-cp27-cp27m-win_amd64.whl``

One option is to use a Python distribution that has these packages preinstalled, such as [Anaconda](https://www.continuum.io/downloads); this is not recommended as it can lead to problems with Node.js finding the correct executable file, especially if you use both Python 2.7 and 3.5. 


#### OS X
Install **[HomeBrew](http://brew.sh/)**. Then use HomeBrew to install zeromq and pkg-config:

``brew install zeromq pkg-config``

#### Debian/Ubuntu
Install the **npm and nodejs packages**:

``sudo apt-get install apt-get install -y curl && \
        curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
        apt-get install -y nodejs``

*Note:* You can largely follow the [Dockerfile](https://github.com/DiscoveryAnalyticsCenter/Nebula/blob/master/Dockerfile) to install this project via command line. Please refer to it if you have any issues during installation.

### Install Node.js packages

Once these platform specific dependencies have be installed, you can install all the required **Node.js modules** using:

``npm install``

*Developer Tip:* on Linux and OS X you may need to use ``sudo``. Additionally, if you have problems with the installation, you may need to change the permissions for the node_modules directory using `chown -R yourusername:yourusername node_modules` (which is discussed more [here](https://github.com/Automattic/node-canvas/issues/1188)).

With this, all the Node dependencies should be installed. 

### Install Python Pipeline Dependenceies

Next, you can install all the **pipeline dependencies** with the command:

``pip3 install ./path/to/Nebula-Pipeline``

*Developer Tip:* If you are going to develop, you can use ``pip3 install -e ./path/to/Nebula-Pipeline``. The `-e` flag will install a link to your development folder instead of copying the files to the `site-packages` directory so may not always need to reinstall when you make changes.

Also, install the **NLTK stopwords** to support UIs that use the Elasticsearch Data Controllers:

``python3 -m nltk.downloader stopwords``

Again, you may need to use `sudo`.

**If you are on Linux and want to support Omniview, you must install a custom sklearn package,** which is only compatible with Linux systems:

``pip3 install -U ./lib/scikit_learn-0.19.dev0-cp27-cp27mu-linux_x86_64.whl``

### Launch the Node.js server

You can now launch the Node.js server by running `sudo npm start` from the root directory. This will start the server locally (listens on port 4040, as defined in `app.js`). You should now be able to connect to the server via `localhost`.

*Developer Tip:* If the code in Nebula-Pipeline has changed, you may not see the changes you made unless you rerun the above `pip install` commands.

*Developer Tip:* If you decide to use a different port for the Node.js server (which is defined in app.js), such as port 8081, you would access the URL as `localhost:8081`.

## User Guide

All accessible web clients are located in the Nebula-UIs folder. The files in this folder are exposed in the web server through the `/` URL. For example, the CosmosTwitter client can be accessed via `/CosmosTwitter.html`. Navigating to the root page will return the default client, `/index.html`.

Multiple clients of the same type can be opened simultaneously, and all clients will be synched together.

When each client connects to the server, it can specify which pipeline to load, which are described below. This pipeline is then started by the Node.js server, by spawning a Python instance. Each pipeline communicates with the Node.js server via a specified port number. These port numbers start at 5555 and increment with each additional pipeline instance spawned. The server automatically connects to the pipeline instance once it is started.

# Developer Notes

## package.json
This is the configuration file for the project. It contains project configuration parameters and the project dependencies that get installed with `npm install`.

## app.js
This is the main entry point of the server. It creates a server listening on port 4040.

## nebula.js
The `nebula` Node.js module contains the heart of the logic pertaining to the visualizations and pipelines. The ports to run the pipeline on and the data to be visualized for each pipeline are hard coded within this module. It also handles the core WebSocket logic by listening for incoming WebSocket connections on the web server, handling tracking rooms and clients, and synching messages between them. It is loaded as a module from app.js.

The current logical flow of the application can be described as follows:

* A client initiates a Socket.io connection to the server, handled by the `io.on('connection')` callback.
* The client requests to join a room, providing a room name and a pipeline run in that room. This is handled by the `socket.on('join')` callback.
* If the room does not exist, create it, and spawn an Python instance of the specified pipeline, using the arguments hard coded for that pipeline at the top of `nebula.js`.
    * If the room does exist, add this user to that room and do not start any new pipeline.
* A connection is initiated with the new pipeline instance, currently done through ZeroMQ sockets using JSON messages.
* The server then listens to certain messages from the client, as described below.

There are four types of message the server and pipelines listen to from clients:

* `action`: This is the only message that is not forwarded to the pipeline. `action` messages represents interactions that occur within the visualization that should be sent to any other web clients if multiple are open in the same room.
* `update`: This message is what triggers an iteration of the pipeline to occur. Information about the type of interaction that occurred is passed with this message and forwarded on to the pipeline.
* `get`: This message is directly forwarded to the pipeline to retrieve raw data.
* `reset`: This message is directly forwarded to the pipeline (like the `get` message), and any state stored on the server for the room is cleared as well.

## pipelines/
This folder contains all the pipeline instances currently implemented, which are:
* `cosmos`: Contains an ActiveSetModel and a SimilarityModel, and works with both the CosmosD3 and CosmosRadar clients
* `composite`: Works similarly to the `cosmos` pipeline with the exception that attributes are displayed as well as observations
* `twitter`: Works similarly to the `cosmos` pipeline with the exception that it connects to a Twitter database. Access and consumer tokens must be set for this to work (see [here](https://dev.twitter.com/oauth/overview) for instructions on creating these keys)
* `espipeline`: Works similarly to the `cosmos` pipeline with the exception that it connects to an Elasticsearch database
* `andromeda`: Contains an ActiveSetModel and an AndromedaModel (which extends the SimilarityModel)
* `sirius`: Contains an ImportanceModel and a SimilarityModel. While computationally similar to Cosmos, the visualization and interactions therein are fundamentally different, emphasizing symmetry in the visualization of and interactions with both observations and attributes
* `centaurus`: Works similarly to the `sirius` pipeline with the exception that it enables foraging (like `cosmos` does).

## data/
This folder contains the data to be used by any of the aforementioned pipelines. The data is split between text, highD, debug, and customCSV.

## public/
This folder contains any files intended for the client. Anything in this folder is accessible from the web server. Currently not really used for anything, as all the important exposed files are in the CosmosD3 folder.

## routes/
Contains all REST logic, which currently only forwards the root path to `/cosmos/CosmosD3.html`. However, the forwarding of the corresponding `CosmosD3.js` file that is necessary to properly use the Cosmos interface has been broken, so the full URL (`/cosmos/CosmosD3.html`) should be used instead.



## Nebula-UIs
This contains all the HTML, Javascript, and CSS files necessary for the web visualization clients, which are detailed below.

### Andromeda

**Andromeda.html** uses **Andromeda.js** and **Andromeda.css**. This client creates a layout with one panel showing similarities between all data points using WMDS, with a side panel displaying the attributes and their weights. When data points are moved or attributes weights are manipulated, the layout is updated with re-calculated similarities.

This visualization is a newer version of the original **AndromedaClassic.html** (and its associated **AndromedaClassic.js**).

### CosmosD3

**CosmosD3.html** uses **CosmosD3.js** and **Cosmos.css**. It implements a layout with one panel for a WMDS projection of documents (similar to Andromeda), with a side panel for further information about a selected document. Text queries (i.e., explicit queries) can be used to bring in data. OLI updates and interactions with the information panel (i.e., implicit queries) can also bring new data into the visualization automatically.

#### Related Deprecated Visualizations

A number of 3D and immersive visualizations as well as a Twitter visualization have been developed that are no longer being actively used. However, we have kept these visualizations and retained at least some basic functionality/connectivity in case we decide to develop these further.

##### \[Deprecated\] Cosmos Twitter

**CosmosTwitter.html** uses **CosmosTwitter.js** and **Cosmos.css**. While the visualization is very similar to CosmosD3, it loads the Twitter pipeline to enable integration with Twitter data. The access and consumer tokens must be set in the Twitter pipeline for this to function properly.

To make this visualization work properly again, the TwitterDataController in the Nebula-Pipeline module must be updated.

##### \[Deprecated\] Oculus with Pipeline

This visualization only needs **Oculus with Pipeline.html** to display an immersive 3D version of the CosmosD3 visualization compatible with the Oculus.

##### \[Deprecated\] Photon2

This visualization only needs **Photon2.html** to display a 3D version of the CosmosD3 visualization using X3DOM.

###### \[Deprecated\] Photon
This visualization only needs **Photon.html** to display a 3D version of the CosmosD3 visualization using X3DOM. This visualization is the predecessor to Photon2.

##### \[Deprecated\] Andromeda X3DDOM
**andromeda - x3dom.html** uses **andromeda - x3dom.js** to display a 3D version of CosmosD3 using X3DOM.

### Cosmos Elasticsearch

**Elasticsearch.html** uses **Elasticsearch.js** and **Cosmos.css**. The layout looks nearly identical to CosmosD3, but the Data Controller connects to an Elasticsearch database. Currently, implicit querying is not yet implemented.

This visualization can appear laggy or unresponsive if the Elasticsearch database has performed too much indexing. If this is the case, then the Nebula-Elasticsearch module should be reset to remove these extra indices and then restarted. An easy way to do this is to delete and then reinstall the Nebula-Elasticsearch module.

### [Buggy] Cosmos Radar

**CosmosRadar.html** uses **CosmosRadar.js** and **Cosmos.css**. The layout produced is a modification of CosmosD3 so that document similarity is mapped in only one dimension, an angular component, and the document relevance is mapped to the distance from the center. This visualization is based on the [Intent Radar by Ruotsalo et al.](https://dl.acm.org/doi/abs/10.1145/2505515.2505644?casa_token=1k3Jd-8nGbwAAAAA:dKv-EAAXkXJS3s3s-Lxz0vXEoNXthtRB69TjEuaydyw3zabiKh4-Us15nt0a6rDI-yDirPUIvwuL)

This visualization does not properly account for document relevance when performing OLI. The inverse function(s) of one or more modules would need to be updated to fix this.

### [Buggy] Cosmos Composite

**CosmosComposite.html** uses **CosmosComposite.js** and **Cosmos.css**. The layout produced is a modification of CosmosD3 in which extracted entities are mapped into the same WMDS projection as the documents themselves. This visualization is based on the [Data Context Map by Mueller et al.](https://ieeexplore.ieee.org/abstract/document/7194836?casa_token=sis8-ae8g74AAAAA:id-TgCxD_N-gj0nAN4k-yx0J9lHt4ni84zIZUxu2YDwrsDGpJ5n8kIYxRo01zm5PLsGNDACuZw)

Currently, interaction with the attributes is broken. Attempting to do so may result in an error that crashes the pipeline.

### SIRIUS

This visualization is similar to Andromeda in terms of the underlying math that is used in the Models. However, the visualization simultaneously displays both observations and attributes in separate panels. The same interactions are afforded in each panel.

### Centaurus

This visualization is based on SIRIUS but includes the ability to forage for more data using both keyword search foraging and automated foraging (similar to CosmosD3).

### Establishing Server and Pipeline Communications

Most of the above clients use **InitializeSession.js** to manage sessions/rooms, such as uploading custom data files or initializing a new pipeline. Much of this is accomplished using socket.io to send messages from each of the above interfaces to the nebula.js server. Additional details behind this communication is detailed below.


### Code Hygiene

It is generally expected that new development in any of these existing interfaces or in a new interface will follow these practices:

- **HTML file**: Contains the skeleton code to generate the desired visualization as well as references/links to any necessary JavaScript or CSS files. These HTML files should be very basic and relatively empty; anything that needs to be dynamic in any way should probably be defined in the associated JavaScript file. Generally, this file MUST reference InitilizeSession.js to establish its connection with the server and any associated pipeline. NO CSS styles should be defined in this file.
- **CSS file**: Contains the CSS styles that are generally or commonly used in the visualization.
- **InitializeSession.js**: Generally, all code pertaining to initializing a new pipeline or connecting to an existing pipeline should be contained in this file. This includes telling the server that which pipeline the client wants to connect to (whether it’s an existing pipeline or a new pipeline) or uploading a custom dataset.
- **JavaScript file(s)**: Contains the code to render any dynamic portions of the visualization and handle the interactions therein. This file must establish an initial connection with the server by calling:
   ```javascript
   var socket = io.connect();
   ```

   Additionally, it should define a global variable called `ui` to define what type of pipeline should be constructed to match this interface. All other code pertaining to user interactions or dynamic pieces of the visualization should be defined here. As explained below, this includes code to communicate user interactions with the server (via `socket.emit(...)` and `socket.on(...)`).


### Using Socket.io to Communicate with the Server

Here we describe all the necessary pieces to establish your interface as a new client and to communicate with the server and pipeline.

All communication with the server is done through a WebSocket connection. This connection is created by first including the socket client script by including the following within the HTML file for the given interface:
```javascript
<script src="/socket.io/socket.io.js"></script>
```

Then a connection can be initiated in the associated JavaScript file by calling:
```javascript
var socket = io.connect();
```
Note that this line of code **CANNOT** be in InitializeSession.js due to how Socket.io establishes its connection to your interface.

Then, you must tell the server that you want to join and room. This is done by emitting the `join` message, which includes the name of the room you wish to join (called “default” in the example below), your user ID (typically the ID of the socket), the name of the pipeline you want to run, and any additional arguments for that pipeline. For example, to create or join a room using the `cosmos` pipeline (which does not need any additional arguments), you would call
```javascript
socket.emit('join', 'default', socket.id, 'cosmos');
```
If you created a 3D client and wanted the cosmos pipeline to output positions in 3D (which does require additional arguments), you can indicate that with:
```javascript
socket.emit('join', 'default', socket.id, 'cosmos', {'low_dimensions': 3});
```
The arguments available are dependent on the pipeline you are running. However, this code **ALWAYS** should be in InitializeSession.js.

You can then inform the server of simpler user interactions (e.g., selecting a datapoint) using `action` messages, inform the server of more complicated interactions (e.g., OLI) using the `update` message, request raw data directly from the data controller using the `get` message, or reset the pipeline using the `reset` message. (More details on these messages are provided in the Nebula and Nebula-Pipeline documentation.) Each of these messages are sent to the server using the same `emit` function in Socket.io, which takes the name of the message as its first parameter and any additional parameters passed as necessary. For example, initiating a text query in the `cosmos` pipeline would be done by calling:
```javascript
socket.emit('update', {type: "search", query: <search query>});
```
Note that since these `emit` functions are based on user interactions, they should **ALWAYS** be used in the associated JavaScript file for the interface (i.e., **NOT** InitializeSession.js). The server then handles this message as necessary.

If the server responds to one of the above messages, you must create callbacks to receive the server's response. This is accomplished through the same four types of messages described above using the `on` function in Socket.io:
```javascript
socket.on('action', function(data) {...});
socket.on('update', function(data) {...});
socket.on('get', function(data) {...});
socket.on('reset', function() {...});
```
Note that since these `on` functions are meant to respond to user interactions, they should **ALWAYS** be used in the associated JavaScript file for the interface (i.e., **NOT** InitializeSession.js).

## Nebula-Pipeline

This part of the project was originally created with [Nodeclipse](https://github.com/Nodeclipse/nodeclipse-1)
 ([Eclipse Marketplace](http://marketplace.eclipse.org/content/nodeclipse), [site](http://www.nodeclipse.org))   

Nodeclipse is free open-source project that grows with your contributions.

### Pipeline components
Each of the three main components, Models, Data Controllers, and Connectors, have a base class defined within the `pipeline` module. New instances of these components simply need to overwrite the methods defined in these classes as they are described in the comments. The structure of a pipeline can be seen in the following figure:

![Unable to load figure](Nebula-Pipeline/docs/img/generalpipeline.jpg)

### Data Controller
The Data Controller mediates access to whatever underlying data is being visualized. While essentially operating as a Model itself, it has one extra key function: its `get` method. Visualizations can use this `get` method to directly access the underlying data or metadata without having to run an iteration of the pipeline.

#### Current Data Controllers

##### CSVDataController
This data controller loads high dimensional data from a CSV file, where each row indicates a data point and each column represents an attribute of the data. The first row should be attribute names, and the first column should be an ID for each point. Optionally, when working with text data, a folder containing the raw text of each document can be specified. This folder should contain a text file for each document, with a filename of "*id*.txt". Then the raw text can be queried for from the visualization using a `get` command.

##### \[Deprecated\] TwitterDataController
This streams live tweets into the visualization using the Twitter API. The filter to search for can be set through an interaction, and all tweets that come in matching that filter are then buffered and eventually sent to the visualization. To use this data controller again, it needs to be properly reconnected to a Twitter account.

##### ESDataController
This connects the pipeline to an Elasticsearch database, which must be run separately (using the Nebula-Elasticsearch repository). This data controller and the database itself communicate with each other over a predefined port.

### Models
Models are the main data processing components of a pipeline. They have two main pieces: the forward algorithm and the inverse algorithm. User interactions trigger running all inverse algorithms along the pipeline in order to interpret the interaction. Each Model is capable of short circuiting itself, which cuts the pipeline short and starts the forward pipeline immediately from that same Model. The forward algorithms for each model use the new parameters learned by the inverse algorithms. After each forward algorithm is run, the resulting data is passed back to the visualization through the connector.

#### Current Models

##### SimilarityModel
Performs forward and inverse MDS projection of the data. The forward projection is done using the sklearn package. The inverse projection is done using a Java library we created. This algorithm is in the process of being ported to Python, so this Java code will soon no longer be required. The inverse projection results in a new set of attribute weights, which are used during the next forward projection of the data.

##### CompositeModel
Extends the SimilarityModel by adding attributes to the project data. It uses a [composite matrix approach](https://ieeexplore.ieee.org/abstract/document/7194836?casa_token=sis8-ae8g74AAAAA:id-TgCxD_N-gj0nAN4k-yx0J9lHt4ni84zIZUxu2YDwrsDGpJ5n8kIYxRo01zm5PLsGNDACuZw), forming a pairwise distance matrix that includes attributes as data points. Only attributes that have a certain amount of weight to them are included. The inverse projection is the same as the SimilarityModel.

##### AndromedaModel
Extends the SimilarityModel to provide more of the features from the Andromeda tool. It adds the interaction of manipulating attribute weights directly.

##### ActiveSetModel
Uses a relevance-based approach to filter down a large set of data points to a smaller set to be visualized. It interprets three basic interactions: text queries that are matched to attribute names to influence weights, user indicated changes to document relevance to affect the weights of attributes in that document, and document deletion.

An "active set" of documents is stored, which is all the documents currently being considered to send down the pipeline. The most relevant documents are placed into the "working set", which is what is currently being seen in the visualization.

##### ImportanceModel
This model is similar to the ActiveSetModel with the exception that this model relies on relevance calculations to filter documents and attributes to be visualized. Interactions may also occur on either the documents or the attributes.

##### CorpusSetModel
Similar to the ActiveSetModel, but acts as an asynchronous model, so all computations are done in a background thread and not within the synchronous pipeline loop. It is designed to be used in conjunction with the ActiveSetModel. This allows for a larger set of documents to be iterated over without affecting the response time of the pipeline. The main limitation is that results from this model will always be at least one interaction behind, so a text query may result in new documents placed in the "active set", but they cannot be moved to the "working set" and sent to the visualization until the next interaction occurs.

### Connector
The Connector is in charge of communication between the pipeline and the visualization. It can use whatever means its decides to allow visualizations to run algorithms within the pipeline and retrieve data directly through the `get` functionality.

#### Current Connectors

##### ZeroRPCConnector
Establishes a zerorpc server with RPC calls for ``update``, ``get``, and ``reset``. Allows for simple communication with a Node.js server, but does not allow for asynchronous pushes from the pipeline.

##### ZeroMQConnector
Creates a ZeroMQ PAIR socket and listens for a connection. Messages are encapsulated into an RPC-like fashion, but it allows for asynchronous pushes.

### Creating a Pipeline
Creating a pipeline is straight forward. First, you create a new instance of a pipeline. Then, you create instances of all the models you want, along with a data controller and a connector. Finally, you add all these pieces to the pipeline and start it. This is all exemplified in the following example:

```python
# Create a Pipeline object from the nebula.pipeline module
pipeline = nebula.pipeline.Pipeline()

# Create an ActiveSetModel object from the nebula.model module, starts out empty
relevance_model = ActiveSetModel()
    
# Create a SimilarityModel object from the nebula.model module, which does 
# forward and inverse MDS
# projections and stores the current set of similarity weights
similarity_model = SimilarityModel()

# Create a CSVDataController object from the nebula.data module, providing
# a CSV file to load data from and the path to a folder containing the raw
# text for each document. 
# IMPORTANT: The CSV file should not be changed hereafter
data_controller = CSVDataController(csvfile, raw_folder)

# Create a ZeroMQConnector object from the nebula.connector module, which
# defines a method for listening for the three types of user defined 
# messages: update, get, and reset. 
connector = nebula.connector.ZeroMQConnector(port=int(sys.argv[1]))

# Next we add the models to the pipeline. New models would be added here.
# The order that the models are
# added is the order in which they are executed in the forward pipeline.
# IMPORTANT: They are executed in reverse order in the inverse pipeline
pipeline.append_model(relevance_model)
pipeline.append_model(similarity_model)
    
# Note: a pipeline contains exactly one data controller
pipeline.set_data_controller(data_controller)
    
# Note: a pipeline contains exactly one connector
pipeline.set_connector(connector)
    
# Starts the pipeline, running the setup for the data controller and each
# model, and then tells the connector to start listening for connections.
# The pipeline can take command line arguments to set user defined model
# parameters.
pipeline.start(sys.argv[4:])
```

This projet contains several data controllers, models, and connectors available for use. Here we describe the basics of each. You can find more details in the documentation for each module. However, note that any additions to the module may require rerunning `pip install -e .`.


### Python Modules and Code

Development of new components or modifying current ones is fairly simple. The project is structured as a single Python package, called `nebula`. Within this package are four main modules: `pipeline`, `data`, `model`, and `connector`. The purpose of each are described below.

#### nebula.pipeline
This module contains the `Pipeline` class which has all the logic for putting together and running a pipeline. It mediates communication between each piece of the pipeline, and is the core piece of the framework. As seen in the example above, to start a pipeline, you simply need to instantiate a `Pipeline` object, add the necessary modules to it, and tell it to start.

This module also contains the base classes for the three main modules, `DataController`, `Model`, and `Connector`. Each implementation of one of these modules should extend the appropriate base class and override the necessary methods. All methods that can be overridden to affect the behavior of a module is listed out in each base class.

#### nebula.data
This module contains all the current implementations of data controllers. New data controllers should be added to the `data_controller` directory. This directory also contains `nltkStopwords.txt`, which is used by the TwitterDataController to filter out additional stopwords from tweets. The current data controllers are listed above in the User Guide.

#### nebula.model
This module contains all the current implementations of models, which are listed above. New modules should be added to the `model` directory.

#### nebula.connector
This module contains all the current implementations of connectors, which are listed above. This file can be modified to change these connectors or add new ones.

#### Additional files
The `java/` folder contains the Java libraries used for the inverse MDS calculation within the SimilarityModel. This library comes from the Nebula-Java project, and will hopefully be replaced with direct Python code.
