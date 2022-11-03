import spawn from "child_process";
import fs, { symlinkSync } from "fs";
import * as readline from 'node:readline';
import async from "async";
import zmq from "zeromq";
// import readline from "linebyline";
import getPort from "get-port";
import express from "express";
import { Server } from "socket.io";
import { createServer } from "http";


/* Load the databases we need */
//var monk = require('monk');
//var db = monk('localhost:27017/nodetest');
//var datasets = monk('localhost:27017/datasets');

/* Export the Nebula class */
// module.exports = Nebula;
// module.exports = io;
// export default(Nebula);
// export default(io);



/* Location of the data for the Crescent dataset */
var textDataPath = "data/text/";
var crescentRawDataPath = textDataPath + "crescent_raw";
var crescentTFIDF = textDataPath + "crescent tfidf.csv";
var crescentTopicModel = textDataPath + "crescent_topics.csv";

/* Location of the data for the UK Health dataset */
var ukHealthRawDataPath = textDataPath + "uk_health_raw";
var ukHealthTFIDF = textDataPath + "uk_health.csv";

/* Map CSV files for text data to raw text location */
var textRawDataMappings = {};
textRawDataMappings[crescentTFIDF] = crescentRawDataPath;
textRawDataMappings[crescentTopicModel] = crescentRawDataPath;
textRawDataMappings[ukHealthTFIDF] = ukHealthRawDataPath;

/* The pipelines available to use */
var flatTextUIs = ["cosmos", "composite", "sirius", "centaurus"];
var pipelines = {
    andromeda: {
        file: "pipelines/andromeda.py",
        defaultData: "data/highD/Animal_Data_study.csv"
    },
    cosmos: {
        file: "pipelines/cosmos.py",
        defaultData: textDataPath + "crescent tfidf.csv"
    },
    sirius: {
        file: "pipelines/sirius.py",
        defaultData: "data/highD/Animal_Data_paper.csv"
    },
    centaurus: {
        file: "pipelines/centaurus.py",
        defaultData: "data/highD/Animal_Data_paper.csv"
    },
    twitter: {
        file: "pipelines/twitter.py",
    },
    composite: {
        file: "pipelines/composite.py",
        defaultData: textDataPath + "crescent tfidf.csv"
    },
    elasticsearch: {
        file: "pipelines/espipeline.py",
        args: []
    },
    omniview: {
        file: "pipelines/omniview.py",
        args: []
    }
};

/* The locations of the different types of datasets on the server */
var textDataFolder = "data/text/";
var highDDataFolder = "data/highD/";
var customCSVFolder = "data/customCSV/";

var sirius_prototype = 2;

// An array to track the ports being processed to eliminate race conditions
// as much as possible
var portsInProcess = [];

var nextSessionNumber = 0;
var usedSessionNumbers = [];


/* Nebula class constructor */
export default function Nebula(clientio, pipelineAddr) {
    /* This allows you to use "Nebula(obj)" as well as "new Nebula(obj)" */
    if (!(this instanceof Nebula)) {
        return new Nebula(clientio);
    }

    /* The group of rooms currently active, each with a string identifier
     * Each room represents an instance of a visualization that can be shared
     * among clients.
     */
    this.rooms = {};
    this.clientio = clientio;
    //this.pythonio = pythonio;

    /* For proper use in callback functions */
    var self = this;

    /* Accept new WebSocket clients */
    clientio.on('connection', function (socket) {
        console.log("new connection finally!");

        //This was used to test the connector connection    
        socket.on('testing', function () {
            console.log("Python connection established!");
        });

        /* When a client requests the list of rooms, send them the list */
        socket.on('list.sessions', function () {
            console.log("listing sessions")
            console.log("number of sessions: " + JSON.stringify(Object.fromEntries(clientio.sockets.adapter.rooms)))
            socket.emit('list.sessions.response', clientio.sockets.adapter.rooms);
        });

        /* When clients disconnect, remove them from the room. If the room is
         * now empty, delete it.
         */
        function disconnectClient() {
            var name = socket.roomName;
            var roomData = self.rooms[name];

            console.log(socket.roomName + ': Client disconnecting');

            if (roomData && roomData.hasOwnProperty("count")) {
                roomData.count -= 1;
                console.log(socket.roomName + ": Count of room = " + roomData.count);

                if (roomData.count <= 0) {
                    console.log(socket.roomName + ": Room now empty");

                    // Get the session number of the current session
                    var sessionNumber;
                    var index = name.length - 1;
                    var sessionNumberFound = false;
                    while (!sessionNumberFound && index >= 0) {
                        var number = Number(name.substring(index, name.length));
                        if (Number.isNaN(number)) {
                            sessionNumber = Number(name.substring(index + 1, name.length))
                            sessionNumberFound = true;
                        }
                        index--;
                    }

                    // Remove the room number associated with this room from
                    // usedSessionNumbers
                    var sessionNumIndex = usedSessionNumbers.indexOf(sessionNumber);
                    var usedSessionNums1 = usedSessionNumbers.slice(0, sessionNumIndex);
                    var usedSessionNums2 = usedSessionNumbers.slice(sessionNumIndex + 1, usedSessionNumbers.length);
                    usedSessionNumbers = usedSessionNums1.concat(usedSessionNums2);

                    // Kill the Python script associated with the empty room
                    roomData.pipelineInstance.stdin.pause();
                    roomData.pipelineInstance.kill('SIGKILL');

                    // Remove the empty room from the list of rooms
                    delete self.rooms[name];

                    // Delete the room's CSV file
                    deleteFile(customCSVFolder + name + "_data.csv");

                    // Make sure the room is no longer maintained by Socket.io
                    delete clientio.sockets.adapter.rooms[name];
                }
            }
        };

        socket.on('disconnect', disconnectClient);

        // When we have a client who is still communicating via Socket.io but
        // wants to change to a different session/dataset, we need to use a
        // different message than "disconnect" since this has special meaning
        // and will cease all communications with that specific client
        socket.on('session-change', disconnectClient);


        /* When the client starts trying to select a file, provide a list of
         * possible files to choose from
         */
        socket.on('getDefaultFileList', function (isTextOnlyUI, ui) {
            if (ui == "radar") {
                ui = "cosmos";
            }

            // Grab all the text CSV files
            var textDataList = fs.readdirSync(textDataFolder)
                .filter(data => data.endsWith(".csv"))
                .map(data => data = "text/" + data);

            // Grab the highD text files if the UI can support non-text data
            var highDDataList = []
            if (!isTextOnlyUI) {
                highDDataList = fs.readdirSync(highDDataFolder)
                    .filter(data => data.endsWith(".csv"))
                    .map(data => data = "highD/" + data);
            }

            // Provide the list of available datasets to the client
            socket.emit("receiveDefaultFileList",
                textDataList.concat(highDDataList),
                pipelines[ui]["defaultData"].substring("data/".length));
        });

        // Use the csvFilePath to store the name of a user-defined CSV file
        var csvFilePath = null;

        /* Helper function to tell the client that the CSV file is now ready for them
        * to use. They are also sent a copy of the data
        */
        var csvFileReady = function (csvFilePath) {

            // Let the client know that the CSV file is now ready to be used on
            // the server
            socket.emit("csvDataReady");

            // Prepare to parse the CSV file
            var csvData = [];
            const rl = readline.createInterface({
                input: fs.createReadStream(csvFilePath),
                crlfDelay: Infinity
            });
            //const rl = readline(csvFilePath);

            // Print any error messages we encounter
            rl.on('error', function (err) {
                console.log(socket.roomName + ": Error while parsing CSV file: " + csvFilePath);
                console.log(err);
            });

            // Read each line of the CSV file one at a time and parse it
            var columnHeaders = [];
            var firstColumnName;
            rl.on('line', function (data) {
                var dataColumns = data.split(",");

                // If we haven't saved any column names yet, do so first
                if (columnHeaders.length == 0) {
                    columnHeaders = dataColumns;
                    console.log(columnHeaders)
                    firstColumnName = columnHeaders[0];
                }

                // Process each individual line of data in the CSV file
                else {
                    var dataObj = {};
                    var i;
                    for (i = 0; i < dataColumns.length; i++) {
                        var key = columnHeaders[i];
                        var value = dataColumns[i];
                        dataObj[key] = value;
                    }
                    csvData.push(dataObj);
                }

            });

            // All lines are read, file is closed now.
            rl.on('close', function () {

                // On certain OSs, like Windows, an extra, blank line may be read
                // Check for this and remove it if it exists
                var lastObservation = csvData[csvData.length - 1];
                console.log(csvData.length)
                // console.log(csvData)
                var lastObservationKeys = Object.keys(lastObservation);
                if (lastObservationKeys.length = 1 && lastObservation[lastObservationKeys[0]] == "") {
                    csvData.pop();
                }

                // Provide the CSV data to the client
                socket.emit("csvDataReadComplete", csvData, firstColumnName);
            });
        };

        /* When the client sends a "setData" message with the data and room name,
         * generate a new file using the room name that contains the given data.
         * Set the csvFilePath variable appropriately
         */
        socket.on('setData', function (data, room) {
            // Create the csvFilePath
            csvFilePath = customCSVFolder + room + "_data.csv";
            // Set exec to be a function that calls the command line
            var exec = require('child_process').exec;

            // Initialize errors to be an empty array to capture any errors
            var errors = [];
            // Create the command to use on the command line
            var command = "echo \"" + data + "\" > " + csvFilePath;

            // Execute the command and cature any errors or printouts
            var childProcess = exec(command, "-e", function (error, stdout, stderr) {
                // Print out any stdout captured to the console
                if (stdout) {
                    console.log(socket.roomName + ': Creating CSV file stdout: ' + stdout);
                }

                // Put any errors in the errors array
                if (error) {
                    console.log(socket.roomName + ': Creating CSV file error: ' + error);
                }

                // Put any errors in the errors array and print them out to
                // the console
                if (stderr) {
                    console.log(socket.roomName + ': Creating CSV file stderr: ' + stderr);
                }
            });

            childProcess.on("close", function () {
                // Only emit the "csvDataReady" message to the client if no errors
                // were encountered while attempting to create the custom CSV file
                if (errors.length == 0) {
                    csvFileReady(csvFilePath);
                }
            });
        });

        /* Allows the client to specify a CSV file already on the server to use */
        socket.on("setCSV", function (csvName) {
            csvFilePath = "data/" + csvName;
            csvFileReady(csvFilePath);
        });

        /*
         * Allows the server to be in control of session names
         */
        socket.on("getSessionName", function (ui) {
            // Create the new session name and send it back to the UI
            var sessionName = ui + nextSessionNumber;
            socket.emit("receiveSessionName", sessionName);

            // Keep track of used session numbers
            usedSessionNumbers.push(nextSessionNumber);

            // Determine the next session number. If we're getting too close to
            // the MAX_VALUE, start looking at old session numbers to see if an
            // old number can be used
            if (nextSessionNumber == Number.MAX_VALUE || (nextSessionNumber + 1) > Number.MAX_VALUE) {

                // Start back at 0 and check for session numbers that are no
                // longer being used. 0 would be the oldest session number, and
                // therefore is the most likely to no longer be used. Continue
                // incrementing until an unused session number is found or we
                // reach MAX_VALUE again
                // NOTE: THERE IS NO PROTECTION AGAINST NOT BEING ABLE TO FIND
                // A NEW SESSION NUMBER
                nextSessionNumber = 0;
                while (usedSessionNumber.indexOf(nextSessionNumber) >= 0 &&
                    nextSessionNumber < Number.MAX_VALUE) {
                    nextSessionNumber++;
                }
            }
            else {
                nextSessionNumber++;
            }
        });

        /* Lets a client join a room. If the room doesn't next exist yet,
         * initiate it and send the new room to the client. Otherwise, send
         * the client the current state of the room.
         */
        socket.on('leave', function () {
            var roomname = socket.roomName;
            socket.room.count -= 1;
            socket.leave(socket.roomName);
            socket.emit('leave', roomname);

            if (socket.room.count <= 0) {
                var filePath = customCSVFolder + roomname + "_data.csv";
                deleteFile(filePath);
            }

        });

        // function to delete a file
        function deleteFile(filePath) {
            fs.stat(filePath, function (err, data) {
                if (err) {
                    console.log(socket.roomName + ': File ' + filePath + ' does not exist');
                }
                else {
                    fs.unlink(filePath, function (err) {
                        if (err) {
                            return console.error(socket.roomName + ": Error unlinking file: " + err);
                        }
                    });
                }
            });
        }

        /*  a client/ a room. If the room doesn't next exist yet,
         * initiate it and send the new room to the client. Otherwise, send
         * the client the current state of the room.
         */
        socket.on('join', function (roomName, user, pipeline, args) {
            console.log(roomName + ": Join called for " + pipeline + " pipeline");
            socket.roomName = roomName;
            socket.user = user;
            socket.join(roomName);

            var pipelineArgsCopy = [];

            // Beging an asynchronous call so that we can dynamically grab an
            // open port number as well as manipulate csvFilePath approproately.
            // The way that the code is written effectively makes this asynchronous
            // call synchronous
            (async () => {
                if (!self.rooms[roomName]) {
                    var room = {};
                    room.name = roomName;
                    room.count = 1;
                    room.points = new Map();
                    room.similarity_weights = new Map();

                    if (pipeline == "sirius" || pipeline == "centaurus") {
                        room.attribute_points = new Map();
                        room.attribute_similarity_weights = new Map();
                        room.observation_data = [];
                        room.attribute_data = [];
                    }

                    /* Create a pipeline client for this room */
                    // First, grab a valid open port
                    var port;
                    while (!port || portsInProcess.indexOf(port) >= 0) {
                        // This is the line of code that requires the
                        // asynchronous call
                        port = await getPort();
                    }
                    portsInProcess.push(port);

                    if (!pipelineAddr) {
                        var pythonArgs = ["-u"];
                        if (pipeline in pipelines) {

                            // A CSV file path should have already been set. This
                            // file path should be used to indicate where to find
                            // the desired file
                            if (!csvFilePath) {
                                csvFilePath = pipelines[pipeline].defaultData;
                            }
                            pipelineArgsCopy.push(csvFilePath);

                            // If the UI supports reading flat text files, tell the
                            // pipeline where to find the files
                            if (flatTextUIs.indexOf(pipeline) >= 0) {
                                pipelineArgsCopy.push(textRawDataMappings[csvFilePath]);
                            }

                            // Set the remaining pipeline args
                            pythonArgs.push(pipelines[pipeline].file);
                            pythonArgs.push(port.toString());
                            if (pipeline != "twitter" && pipeline != "elasticsearch" && pipeline != "omniview") {
                                pythonArgs = pythonArgs.concat(pipelineArgsCopy);
                            }
                        }
                        else {
                            pythonArgs.push(pipelines.cosmos.file);
                            pythonArgs.push(port.toString());
                            pythonArgs.push(pipelines.cosmos.defaultData);
                            pythonArgs.push(crescentRawDataPath);
                        }

                        // used in case of CosmosRadar
                        for (var key in args) {
                            if (args.hasOwnProperty(key)) {
                                pythonArgs.push("--" + key);
                                pythonArgs.push(args[key]);
                            }
                        }

                        // Dynamically determine which distance function should be
                        // used
                        if (pythonArgs.indexOf("--dist_func") < 0) {
                            if (pipeline === "twitter" || pipeline === "elasticsearch" ||
                                pipeline === "omniview" ||
                                csvFilePath.startsWith(textDataPath)) {
                                pythonArgs.push("--dist_func", "cosine");
                            }
                            else {
                                pythonArgs.push("--dist_func", "euclidean");
                            }
                        }

                        console.log(socket.roomName);
                        console.log(pythonArgs);
                        console.log("");

                        var pipelineInstance = spawn.spawn("python3", pythonArgs, { stdout: "inherit" });

                        pipelineInstance.on("error", function (err) {
                            console.log(socket.roomName + ": python3.exe not found. Trying python.exe");
                            pipelineInstance = spawn.spawn("python3", pythonArgs, { stdout: "inherit" });

                            pipelineInstance.stdout.on("data", function (data) {
                                console.log(socket.roomName + " Pipeline: " + data.toString());
                            });
                            pipelineInstance.stderr.on("data", function (data) {
                                console.log(socket.roomName + " Pipeline error: " + data.toString());
                            });
                        });

                        /* Data received by node app from python process,
                         * ouptut this data to output stream(on 'data'),
                         * we want to convert that received data into a string and
                         * append it to the overall data String
                         */
                        //check data for one of the 4 commands, else log as below
                        pipelineInstance.stdout.on("data", function (data) {
                            console.log(socket.roomName + " Pipeline STDOUT: " + data.toString());
                        });
                        pipelineInstance.stderr.on("data", function (data) {
                            console.log(socket.roomName + " Pipeline error: " + data.toString());
                        });

                        room.pipelineInstance = pipelineInstance;
                    }

                    /* Connect to the pipeline */
                    pipelineAddr = pipelineAddr || "tcp://127.0.0.1:" + port.toString();


                    /*
                    This is the original code utilizing zmq
                    room.pipelineSocket = zmq.socket('pair');
                    console.log(Object.getOwnPropertyNames(zmq));

                    let sock = new zmq.Socket('pair');
                    room.pipelineSocket = sock;
                    room.pipelineSocket.connect(pipelineAddr);
                    */

                    //Utilizing Socket.io to connect to connector
                    const httpServer = createServer();
                    this.pythonio = new Server(httpServer);
                    httpServer.listen(port);

                    //Setting the new socket for the room
                    room.pipelineSocket = this.pythonio;


                    pipelineAddr = null;
                    portsInProcess.splice(portsInProcess.indexOf(port), 1);

                    room.pipelineSocket.on("connection", function (sock) {
                        sock.on('message', function (data) {
                            self.handleMessage(room, JSON.stringify(data));
                        });
                        invoke(room.pipelineSocket, "reset");
                    })

                    self.rooms[roomName] = socket.room = room;
                }
                else {
                    socket.room = self.rooms[roomName];
                    socket.room.count += 1;

                    if (pipeline == "sirius" || pipeline == "centaurus") {
                        socket.emit('update', sendRoom(socket.room, true), true);
                        socket.emit('update', sendRoom(socket.room, false), false);
                    }
                    else {
                        socket.emit('update', sendRoom(socket.room));
                    }
                }

                // Reset the csvFilePath to null for future UIs
                csvFilePath = null;
            })();
        });

        /* Listens for actions from the clients, tracking them and then
         * broadcasting them to all other clients within the room.
         */
        socket.on('action', function (data, isObservation) {
            if (socket.room) {
                self.handleAction(data, socket.room);

                //emit update actions to other rooms
                if (typeof (isObservation) == "undefined") {
                    socket.broadcast.to(socket.roomName).emit('action', data);
                }
                else {
                    socket.broadcast.to(socket.roomName).emit('action', data, isObservation);
                }
            }
        });

        /* Listens for update requests from the client, executing the update
         * and then sending the results to all clients.
         */
        socket.on('update', function (data, isObservation, prototype, obsFeedback, attrFeedback, obsForage, attrForage) {
            if (socket.room) {
                if (data.type === "oli") {
                    if (typeof (isObservation) == "undefined") {
                        invoke(socket.room.pipelineSocket, "update",
                            { interaction: "oli", type: "classic", points: oli(socket.room) });
                    }
                    else {
                        invoke(socket.room.pipelineSocket, "update",
                            {
                                interaction: "oli", type: "classic", points: oli(socket.room, isObservation),
                                docFeedback: obsFeedback, attrFeedback: attrFeedback, docForage: obsForage, attrForage: attrForage,
                                view: isObservation, prototype: prototype
                            });
                    }
                }
                else {
                    data.interaction = data.type;
                    if ("obsFeedback" in data) {
                        data["docFeedback"] = data["obsFeedback"];
                    }
                    if ("obsForage" in data) {
                        data["docForage"] = data["obsForage"];
                    }
                    invoke(socket.room.pipelineSocket, "update", data);
                }
            }
        });

        /* Listens for get requests to get information about the underlying data,
         * such as the original text of the document or the type.
         */
        socket.on('get', function (data, isObservation) {
            if (socket.room) {
                invoke(socket.room.pipelineSocket, "get", data);
            }
        });

        /* Resets the pipeline. */
        socket.on('reset', function () {
            if (socket.room) {
                console.log("reset was called!")
                invoke(socket.room.pipelineSocket, "reset");
                socket.room.points = new Map();
            }
        });
    });
}

/* Handles an action received by the client, updating the state of the room
 * as necessary.
 */
Nebula.prototype.handleAction = function (action, room) {
    if (action.type === "move") {
        if (room.points.has(action.id)) {
            room.points.get(action.id).pos = action.pos;
        }
        else if (typeof (room.attribute_points) != "undefined" && room.attribute_points.has(action.id)) {
            room.attribute_points.get(action.id).pos = action.pos;
        }
        else {
            console.log(room.name + ": Point not found in room for move: " + action.id);
        }
    }
    else if (action.type === "select") {
        if (room.points.has(action.id)) {
            room.points.get(action.id).selected = action.state;
        }
        else if (typeof (room.attribute_points) != "undefined" && room.attribute_points.has(action.id)) {
            room.attribute_points.get(action.id).selected = action.state;
        }
        else {
            // Not sure what this condition should be...
            // Use to check typeof(console) != "undefined" which doesn't make sense
            if (typeof (socket) != "undefined") {
                console.log(room.name + ": Point not found in room for select: " + action.id);
            }
            else {
                console.log("Point not for for room in select... " +
                    "socket not defined. (This message may be caused by " +
                    "switching to a new dataset that was uploaded by client)");
            }
        }
    }
    else if (action.type === "sample") {
        if (room.points.has(action.id)) {
            room.points.get(action.id).sample = action.state;
        }
        else if (typeof (room.attribute_points) != "undefined" && room.attribute_points.has(action.id)) {
            room.attribute_points.get(action.id).sample = action.state;
        }
        else {
            console.log(room.name + ": Point not found in room for sampling: " + action.id);
        }
    }
};

/* Handles a message from the pipeline, encapsulated in an RPC-like fashion */
Nebula.prototype.handleMessage = function (room, msg) {
    var obj = JSON.parse(msg.toString());

    if (obj.func) {
        if (obj.func === "update") {
            // returns the data to user based on interaction(search/delete node/move slider)
            this.handleUpdate(room, obj.contents);
        }
        else if (obj.func === "get") {
            //getting data when user clicks a node(document) and send it to the client
            this.clientio.to(room.name).emit("get", obj.contents, true);
        }
        else if (obj.func === "set") {
            this.clientio.to(room.name).emit("set", obj.contents);
        }
        else if (obj.func === "reset") {
            // takes place either when users joins the room or when he hits reset button
            this.clientio.to(room.name).emit("reset");
            invoke(room.pipelineSocket, "update", { interaction: "none", prototype: sirius_prototype });
        }
    }
};

/* Handles updates received by the client, running the necessary processes
 * and updating the room as necessary.
 * This function is called with all updates (search/delete/relevance slider).
 * It stores the data from pipeline to save in the room (points/similarity weights) by calling
 * updateRoom function
 */
Nebula.prototype.handleUpdate = function (room, res) {
    console.log(room.name + ": Handle update called");

    var update = {};
    update.points = [];
    if (res.documents) {
        for (var i = 0; i < res.documents.length; i++) {
            var doc = res.documents[i];
            var obj = {};
            obj.id = doc.doc_id;
            if (doc.display_title) {
                obj.displayTitle = doc.display_title;
            }
            obj.pos = doc.low_d;
            obj.type = doc.type;
            obj.relevance = doc.doc_relevance;
            if (doc.color) {
                obj.col = doc.color;
            }

            if (typeof (room.observation_data) != "undefined") {
                var data = {};
                data.type = 'raw'
                data.id = doc.doc_id
                data.value = doc.doc_attributes
                room.observation_data.push(data)

                obj.type = "observation";
                if (res.ATTRIBUTE.similarity_weights) {
                    for (var j = 0; j < res.ATTRIBUTE.similarity_weights.length; j++) {
                        weight = res.ATTRIBUTE.similarity_weights[j]
                        if (weight.id == obj.id) {
                            obj.relevance = weight.weight
                        }
                    }
                }
            }


            update.points.push(obj);
        }
    }

    if (res.similarity_weights) {
        update.similarity_weights = res.similarity_weights;
    }

    // This grabs the word cloud data, should there be any
    if (res.cloud) {
        update.cloud = res.cloud;
    }

    if (typeof (room.observation_data) != "undefined") {
        updateRoom(room, update, true);
        this.clientio.to(room.name).emit('update', update, true);
    }
    else {
        updateRoom(room, update);
        this.clientio.to(room.name).emit('update', update);
    }

    if (typeof (room.observation_data) != "undefined") {
        var update_attr = {};
        update_attr.points = [];

        if (res.ATTRIBUTE.attr_list) {
            for (var i = 0; i < res.ATTRIBUTE.attr_list.length; i++) {
                var attr = res.ATTRIBUTE.attr_list[i];
                var obj = {};
                var data_attr = {}

                data_attr.type = 'raw'
                data_attr.id = attr.attr_id

                data_attr.value = attr.attribute_docs
                room.attribute_data.push(data_attr)
                obj.id = attr.attr_id;
                obj.pos = attr.low_d;

                obj.type = "attribute";
                if (res.similarity_weights) {
                    for (var j = 0; j < res.similarity_weights.length; j++) {
                        weight = res.similarity_weights[j]
                        if (weight.id == obj.id) {
                            obj.relevance = weight.weight
                        }
                    }
                }

                update_attr.points.push(obj);

            }
        }

        if (res.ATTRIBUTE.similarity_weights) {
            update_attr.similarity_weights = res.ATTRIBUTE.similarity_weights;
        }

        if (typeof (room.observation_data) != "undefined") {
            updateRoom(room, update_attr, false);
            this.clientio.to(room.name).emit('update', update_attr, false);
        }
        //        else {
        //            updateRoom(room, update_attr, false);
        //            this.clientio.to(room.name).emit('update', update_attr, false);
        //        }

    }
};

/* Updates our state for each room upon an update from the pipeline */
/* modifies the values inside room array*/
var updateRoom = function (room, update, view) {
    if (typeof (view) == "undefined" || view) {
        if (update.points) {
            for (var i = 0; i < update.points.length; i++) {
                var point = update.points[i];

                if (room.points.has(point.id)) {
                    if (point.pos) {
                        room.points.get(point.id).pos = point.pos;
                    }
                    if (point.relevance) {
                        room.points.get(point.id).relevance = +point.relevance;
                    }
                }
                else {
                    room.points.set(point.id, point);
                }
            }
        }
        if (update.similarity_weights) {
            for (var i = 0; i < update.similarity_weights.length; i++) {
                var weight = update.similarity_weights[i];

                if (room.similarity_weights.has(weight.id)) {
                    room.similarity_weights.get(weight.id).weight = weight.weight;
                }
                else {
                    room.similarity_weights.set(weight.id, weight);
                }
            }
        }
    }
    else if (!view) {
        if (update.points) {
            for (var i = 0; i < update.points.length; i++) {
                var point = update.points[i];
                if (room.attribute_points.has(point.id)) {
                    if (point.pos)
                        room.attribute_points.get(point.id).pos = point.pos;
                    if (point.relevance)
                        room.attribute_points.get(point.id).relevance = point.relevance;

                }
                else {
                    room.attribute_points.set(point.id, point);
                }
            }
        }
        if (update.similarity_weights) {
            for (var i = 0; i < update.similarity_weights.length; i++) {
                var weight = update.similarity_weights[i];
                if (room.attribute_similarity_weights.has(weight.id)) {
                    room.attribute_similarity_weights.get(weight.id).weight = weight.weight;
                }
                else {
                    room.attribute_similarity_weights.set(weight.id, weight);
                }
            }
        }
    }
};

/* Runs inverse MDS on the points in a room. For inverse MDS,
 * only the selected points are included in the algorithm.
 */
var oli = function (room, isObservation) {
    var points = {};

    if (typeof (isObservation) == "undefined" || isObservation) {
        for (var key of room.points.keys()) {
            var point = room.points.get(key);

            if (point.selected) {
                var p = {};
                p.type = "selected";
                p.lowD = point.pos;
                points[key] = p;
            }
            if (point.sample) {
                var p = {};
                p.type = "sample";
                p.lowD = point.pos;
                points[key] = p;
            }
        }
    }
    else if (!isObservation) {
        for (var key of room.attribute_points.keys()) {
            var point = room.attribute_points.get(key);
            if (point.selected) {
                var p = {};
                p.lowD = point.pos;
                points[key] = p;
            }
        }
    }

    return points;
};

/* Copies the room details we want to send to the client to a new object */
var sendRoom = function (room, isObservation) {
    var modRoom = {};
    if (typeof (isObservation) == "undefined" || isObservation) {
        modRoom.points = Array.from(room.points.values());
        modRoom.similarity_weights = Array.from(room.similarity_weights.values());
    }
    else if (!isObservation) {
        modRoom.points = Array.from(room.attribute_points.values());
        modRoom.similarity_weights = Array.from(room.attribute_similarity_weights.values());
    }
    return modRoom;
};

/* Sends a message to a pipeline, enscapsulating it in an RPC-like fashion */
var invoke = function (socket, func, data) {
    var obj = { "func": func, "contents": data };
    socket.emit('msg', obj);
};
