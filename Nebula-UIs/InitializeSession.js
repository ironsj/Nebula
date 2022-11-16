// Session-related variables
var sessionDropdownName = "Start Here";
var defaultDropdownOption = "Load Data";
var sessions = [defaultDropdownOption]; // A list of rooms to display in the dropdown menu
var currentSessionName = "FAKE"; // A variable to hold the name of the current session
var csvUploadUIs = ["andromeda", "sirius", "centaurus"]; // The UIs that enable custom CSV upload
var textOnlyUIs = ["cosmos", "composite", "radar"]; // UIs that should only process text
var autoConnectUIs = ["twitter", "elasticsearch", "omniview"]; // UIs that should autoconnect (without any dropdown menu)
var isTextData = false; // A flag to track whether the given dataset is text data
var pipelineType; // A variable to hold the type of pipeline to launch
var extraJoinSessionParams = null; // A variable for any extra parameters needed to initialize an appropriate pipeline
var piheight = 0;

// Create a div to hold all session-related elements
var sessionDiv = d3.select("#sessionDiv");
if (!sessionDiv.node()) {
    sessionDiv = d3.select("body").append("div")
        .attr("id", "sessionDiv")
        .attr("class", "container-fluid")
        .style("height", "75px")
        .style("margin-left", "20px")
        .style("position", "relative")
        .style("z-index", "1");
}

// Add a session dropdown menu to the sessionDiv using D3
// When clicked, call sessionDropdownClick
var sessionDiv = sessionDiv.append("div")
    .attr("class", "btn-group");
var dropdownButton = sessionDiv.append("button")
    .attr("type", "button")
    .attr("id", "dropdown")
    .attr("class", "btn btn-default dropdown-toggle")
    .attr("data-toggle", "dropdown")
    .attr("aria-haspopup", "true")
    .attr("aria-expanded", "false")
    .style("margin-top", "-10px")
    .text(sessionDropdownName);
dropdownButton.append("span").attr("class", "caret").style("margin-left", "10px");
dropdownButton.on("click", sessionDropdownClick);

// When a session is selected, call sessionChange
var dropdownOptions = sessionDiv.append("ul").attr("class", "dropdown-menu");
dropdownOptions.append("li").append("a").text(defaultDropdownOption).on("click", sessionChange);

// The function that is called with the session dropdown menu is clicked
// This function updates the list of available sessions to select from
function sessionDropdownClick() {
    // Capture the sessionSelection object
    var e = this;

    // Define the callback for when we receive the list of sessions from the
    // server
    var listSessions = function (allSessions) {
        // Reset the list of sessions. This ensures old/nonexistent sessions
        // are removed
        sessions = [defaultDropdownOption];

        // Iterate through the list of sessions and add them to the list
        for (var session in allSessions) {
            if (session.search(ui) != -1 && session != '' && sessions.indexOf(session) < 0) {
                sessions.push(session);
            }
        }

        // Update the dropdown menu accordingly
        updateDropdownList(e);
    };

    // Create a respose for the "list.rooms.response" to update the list of rooms
    // in the dropdown menu based on the list received from the server
    socket.on('list.sessions.response', listSessions);

    // Tell the server we need a list of rooms, which is handed back using the
    // "list.rooms.response" message
    socket.emit('list.sessions');
}

// The function that is called when a new option is selected from the session
// dropdown menu
// This function handles switching to an existing room or creating a new room
// The custom CSV upload functionality is used if the UI is among the csvUploadUIs list
function sessionChange() {
    // If the UI is CosmosRadar, then we need extraJoinSessionParams to tell the
    // pipeline that we need MDS to project into a 1D low dimensional space
    // instead of 2D. In all other regards, the CosmosRadar pipeline is the same
    // as the CosmosD3 pipeline, so the pipelineType should be "cosmos". In all
    // other cases, pipelineType is the same as the UI.
    var selectedSession = this.text;
    socket.on("receiveDefaultFileList", function (dataList, defaultData) {
        // Define the JQuery dialog that will pop up to allow data selection
        var fileSelect = d3.select("#sessionDiv").append("div")
            .attr("id", "fileSelectOptions")
            .attr("title", "Choose Data")
        fileSelect.append("p")
            .text("Please choose whether you would like to use a " +
                "default dataset or upload your own.");
        fileSelect.append("input")
            .attr("type", "file")
            .attr("id", "fileInput")
            .style("visibility", "hidden");
        fileSelect.append("br");
        fileSelect.append("p")
            .text("Default datasets:");
        var defaultFileSelect = fileSelect.append("div")
            .style("height", "100px")
            .style("border", "1px black solid")
            .style("border-radius", "5px")
            .style("overflow-y", "scroll")
            .append("ul").style("list-style", "none").style("padding", "10px");

        var i;
        var defaultColor = "white";
        var hoverColor = "lightgray";
        var selectedColor = "lightblue";
        var selectedFile = defaultData;
        for (i = 0; i < dataList.length; i++) {
            defaultFileSelect.append("li").text(dataList[i])
                .style("background-color", function () {
                    if (dataList[i] == defaultData) {
                        return selectedColor;
                    }
                })
                .attr("selected", function () {
                    if (dataList[i] == defaultData) {
                        return "True";
                    }
                })
                .on("click", function () {
                    var selectedData = d3.select(this);
                    d3.select(this.parentNode).selectAll("li")
                        .style("background-color", defaultColor)
                        .attr("selected", null);
                    selectedData.style("background-color", selectedColor)
                        .attr("selected", "True");
                    selectedFile = selectedData.text();
                    if (selectedFile.includes("text")) {
                        isTextData = true;
                    }
                    else {
                        isTextData = false;
                    }
                })
                .on("mouseover", function () {
                    d3.select(this).style("background-color", hoverColor);
                })
                .on("mouseout", function () {
                    var thisData = d3.select(this);
                    if (thisData.attr("selected") != "True") {
                        thisData.style("background-color", defaultColor);
                    }
                    else {
                        thisData.style("background-color", selectedColor);
                    }
                });
        }

        // Create the full set of Jquery dialog buttons that might be available
        var dialogButtons = {
            "Use Selected Data": function () {
                piheight = 0;
                createNewSessionName(dropdownOptions, dropdownButton, selectedFile);
                $(this).dialog("close");
            },
            "Upload Data": function () {
                piheight = 0;
                document.getElementById("fileInput")
                    .addEventListener("change", fileSelectWrapper(dropdownOptions), { once: true });
                $('#fileInput').click();
                $(this).dialog("close");
            },
            "Cancel": function () {
                $(this).dialog("close");
            }
        };

        // If the UI does not support custom CSV upload, remove that button from
        // the JQuery dialog
        if (csvUploadUIs.indexOf(ui) < 0) {
            delete dialogButtons["Upload Data"];
        }

        // Show the JQuery dialog
        $(function () {
            $("#fileSelectOptions").dialog({
                resizable: false,
                height: "auto",
                width: 400,
                modal: true,
                buttons: dialogButtons
            });
        });

        // Ensure the dialog box doesn't pop up again when it's not supposed to
        socket.removeListener("receiveDefaultFileList");
    });

    // If the radar interface is being used, specify the low_dimensions returned
    // by WMDS to be 1 and set the pipeline type to "cosmos" (since the pipeline
    // is the same otherwise)
    if (ui == "radar") {
        extraJoinSessionParams = { 'low_dimensions': 1 };
        pipelineType = "cosmos";
    }
    else {
        pipelineType = ui;
    }

    // Handle the creation of a new room
    if (selectedSession == defaultDropdownOption) {

        // If the UI does not enable selecting a particular dataset, just connect
        if (autoConnectUIs.indexOf(ui) >= 0) {
            createNewSessionName(dropdownOptions, dropdownButton);
        }

        // Otherwise, create the JDialog to have the user select/upload data
        else {
            socket.emit("getDefaultFileList", textOnlyUIs.indexOf(ui) >= 0, ui);
        }
    }

    // Handle joining an existing room
    else {
        // Set the nodes array from the UI javascript file to an empty array and
        // delete all nodes from the graph
        piheight = 0;
        nodes = [];
        d3.selectAll(".nodes").remove();

        // Join the existing room
        resetSocketCallbacks();
        if (currentSessionName != "FAKE") {
            socket.emit('session-change');
        }
        currentSessionName = this.text;
        dropdownButton.text(this.text);
        dropdownButton.append("span").attr("class", "caret").style("margin-left", "10px");
        socket.emit('join', this.text, socket.id, pipelineType, extraJoinSessionParams);
    }
};

// A wrapper function for the fileSelect event listener for the "change" event
// for the fileInput button
// This allows the session dropdown menu to be appropriately bound in the event
// listener
function fileSelectWrapper(sessionOptionsDropdown) {
    return function (e) {
        fileSelect(e, sessionOptionsDropdown);
    };
}

// A wrapper for what to do when a CSV file has been chosen
var csvDataReadyFunction = function () {

    // Set the nodes array from the UI javascript file to an empty
    // array and delete all nodes from the graph
    nodes = [];
    d3.selectAll(".nodes").remove();

    // Tell the server that we are joining a new room/session
    resetSocketCallbacks();
    socket.emit('join', currentSessionName, socket.id, pipelineType, extraJoinSessionParams);
}

var csvDataReadCompleteFunction = function (csvContents, firstKey) {
    // We don't want to create a CSV table for Andromeda
    if (ui !== "andromeda") {

        var rawTableContainer = d3.select("body").append("div").attr("class", "container-fluid");

        // Initialize the rawDataTable variable
        var rawTableBtnDiv = rawTableContainer.append("div")
            .attr("class", "col-md-12")
            .style("margin-top", "20px");
        rawTableBtnDiv.append("input")
            .attr("type", "submit")
            .attr("value", "Show Raw Data Table")
            .attr("class", "btn btn-md btn-default")
            .on("click", function () {

                // Remove the button to ensure only 1 table is made
                rawTableBtnDiv.remove();

                // Create a table of the raw CSV data that we have been provided
                var rawDataDiv = rawTableContainer.append("div")
                    .attr("id", "rawDataDiv")
                    .attr("class", "col-md-12")
                    .style("width", function () {
                        return (this.parentNode.clientWidth - 60) + "px";
                    })
                    .style("height", "500px")
                    .style("border", "solid black 1px")
                    .style("margin", "15px 20px 15px")
                    .style("overflow", "scroll");

                var rawDataTable = "<table id='rawDataTable' class='table'>";

                // Sort the keys, leaving the specified key as the first key
                var dataKeys = Object.keys(csvContents[0]);
                dataKeys.splice(dataKeys.indexOf(firstKey), 1);
                dataKeys = [firstKey].concat(dataKeys.sort());

                // Sort the objects
                csvContents.sort((a, b) => (a[dataKeys[0]] > b[dataKeys[0]]) ? 1 : -1);

                // Create the first row of the table
                var firstRow = "<thead><tr>";
                var i;
                for (i = 0; i < dataKeys.length; i++) {
                    firstRow += "<th scope='col'><p>" + dataKeys[i] + "</p></th>";
                }
                firstRow += "</tr></thead>";
                rawDataTable += firstRow;

                // Create each individual row of the table
                rawDataTable += "<tbody>";
                csvContents.forEach(function (csvRow) {

                    var nextRow = "<tr>";

                    // Create each entry for the current row
                    dataKeys.forEach(function (dataKey, i) {

                        var td;
                        var tdEnd;
                        if (dataKey === dataKeys[0]) {
                            td = "<th scope='row'>";
                            tdEnd = "</th>";
                        }
                        else {
                            td = "<td ";
                            tdEnd = "</td>";

                            // Add an ID and tooltip for each td
                            var observationName = csvRow[firstKey];
                            td += "id='o-" + observationName.replace(/\/|<|>|\.| |'/g, "-")
                                + "--a-" + dataKey.replace(/\/|<|>|\.| |'/g, "-") + "' " +
                                "title=\"" + observationName + ", " + dataKey + "\">";
                        }

                        // Put the data in the cell and add the cell to the table row
                        td += "<p>" + csvRow[dataKey] + "</p>" + tdEnd;
                        nextRow += td;

                    });

                    nextRow += "</tr>";
                    rawDataTable += nextRow;
                });

                rawDataTable += "</tbody></table>";
                $(rawDataDiv[0][0]).append(rawDataTable);

                // Highlight row when mousing over
                d3.select("#rawDataTable").selectAll("tr")
                    .on("mouseover", function () {
                        d3.select(this).classed("selected-row", true)
                            .selectAll("td").style("background-color", "yellow");
                    })
                    .on("mouseout", function () {
                        d3.select(this).classed("selected-row", false)
                            .selectAll("td").style("background-color", "white");
                    });

                // Highlight column when mousing over
                // Code adapted from https://stackoverflow.com/questions/38131000/how-to-highlight-a-column-in-html-table-on-click-using-js-or-jquery
                d3.select("#rawDataTable").selectAll("td")
                    .on("mouseover", function () {
                        var index = $(this).index();
                        $("#rawDataTable tr").each(function (i, tr) {
                            $(tr).find('td').eq(index - 1).css("background-color", "yellow");
                        });
                    })
                    .on("mouseout", function () {
                        var index = $(this).index();
                        $("#rawDataTable tr").each(function (j, tr) {
                            $(tr).find('td').eq(index - 1).each(function (k, td) {
                                if (!$(tr).hasClass("selected-row")) {
                                    $(td).css("background-color", "white");
                                }
                            });
                        });
                    });
            });
    }
};

// The function that handles what to do when a custom CSV file is selected
function fileSelect(e, sessionOptionsDropdown) {
    // Get the selected file
    var file = e.target.files[0];

    // Create a FileReader to read the contents of the selected file
    var fileReader = new FileReader();

    // When the FileReader is told to read the file, get the contents of the
    // file, send the contents to the server, wait until the server has
    // completed creating the new file, and join a new room
    var contents;
    fileReader.onload = function (e) {
        // Get the contents of the file
        contents = e.target.result;

        //                contents = contents.split(new RegExp("\n|\r", "g")).filter(function(string) {
        //                    return string != "";
        //                });

        // Get a new room/session name
        socket.removeListener("receiveSessionName");
        socket.on("receiveSessionName", function (sessionName) {
            if (currentSessionName != "FAKE") {
                socket.emit('session-change');
            }
            currentSessionName = sessionName;
            addOptionToSessionDropdown(sessionOptionsDropdown, currentSessionName);
            dropdownButton.text(sessionName);
            dropdownButton.append("span").attr("class", "caret").style("margin-left", "10px");

            // Create a listener for the "csvDataReady" funtion that is sent by
            // the server after it creates the custom CSV file
            // The UI's nodes are reset, the file select buttons are deleted, and
            // the new room is joined
            socket.on("csvDataReady", csvDataReadyFunction);
            socket.on("csvDataReadComplete", csvDataReadCompleteFunction);

            // Send the "setData" message to the server with the contents of the
            // user-specified CSV file and the name of the room/session that
            // will be joined
            socket.emit("setData", contents, currentSessionName);
        });
        socket.emit("getSessionName", ui);
    }

    // Tell the FileReader to read the given file as a text file
    // This triggers the previously defined onload function for the fileReader
    fileReader.readAsText(file);
}

// A helper function to add a new option to the session dropdown menu
function addOptionToSessionDropdown(dropdown, session) {
    // Append the new session to the end of the dropdown menu
    dropdown.append("li").append("a").text(session).on("click", sessionChange);;

    // Append the new session to the sessions array to keep track of which sessions
    // are already in the list
    sessions.push(session);
}

// A helper function to generate a new room/session name, add it to the session
// dropdown menu, make this new session name selected in the dropdown menu, and
// return the name of the new sesson
function createNewSessionName(sessionOptions, sessionButton, selectedFile = null) {
    socket.on("receiveSessionName", function (sessionName) {
        // If we're switching sessions, let the server know
        if (currentSessionName != "FAKE") {
            socket.emit('session-change');
        }
        currentSessionName = sessionName;
        addOptionToSessionDropdown(sessionOptions, sessionName);
        sessionButton.text(sessionName);
        sessionButton.append("span").attr("class", "caret").style("margin-left", "10px");
        if (selectedFile != null) {
            socket.on("csvDataReady", csvDataReadyFunction);
            socket.on("csvDataReadComplete", csvDataReadCompleteFunction);
            socket.emit('setCSV', selectedFile);
        }
        else {
            resetSocketCallbacks();
            socket.emit('join', sessionName, socket.id, pipelineType, extraJoinSessionParams);
        }
    });
    socket.emit("getSessionName", ui);
}

// A helper function to make sure the dropdown menu is showing only the currently
// active session names
function updateDropdownList(dropdownListObject) {
    // Grab all the listed sessions
    var dropdownOptionsList = dropdownOptions.selectAll("li")[0];

    // Remove sessions that are no longer active
    dropdownOptionsList.forEach(function (dropdownOption) {
        if (dropdownOption) {
            var dropdownOptionText = d3.select(dropdownOption).select("a").text();
            if (dropdownOptionText != defaultDropdownOption && sessions.indexOf(dropdownOptionText) < 0) {
                d3.select(dropdownOption).remove();
                i--;
            }
        }
    });

    // Add sessions that aren't listed yet
    for (var i = 1; i < sessions.length; i++) {
        var sessionListed = false;
        dropdownOptionsList.forEach(function (dropdownOption) {
            if (dropdownOption && sessions[i] == d3.select(dropdownOption).select("a").text()) {
                sessionListed = true;
            }
        });

        if (!sessionListed) {
            dropdownOptions.append("li").append("a").text(sessions[i]).on("click", sessionChange);
        }
    }
}

var sessionDisconnect;

window.onload = function () {
    sessionDisconnect = function () {
        socket.on('disconnect', function () {
            d3.selectAll("div").remove();
            d3.select("body").append("h3").text("Your communication with the server " +
                "has been interrupted. Please refresh this page to reconnect.");
        });
    }
    sessionDisconnect();
}

function resetSocketCallbacks() {
    socket.removeAllListeners();
    sessionDisconnect();
    createUISocketCallbacks();
    socket.on("csvDataReadComplete", csvDataReadCompleteFunction);
}
