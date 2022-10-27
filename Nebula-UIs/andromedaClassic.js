// Width and height of the SVG
var width;
var height;
var tempColor;
var radius = 20;
var outerRadius = 60;
// Data to use
var nodes = [];
var sliders = [];
//var handles = getHandles();
var numNodes = nodes.length;
var clientSocketId;

var sourceColorMappings = {
    "Tweet": "url(#stripe_me3)",
    "News": "url(#stripe_me2)"
};

// The name of the UI that is used by InitializeSession.js and nebula.js to
// join rooms/sessions and initialize the pipeline appropriately
var ui = "andromeda";

// Buttons and search box div
var buttonRowDiv = d3.select("body").append("div").attr("class", "container-fluid");
var buttonDiv = buttonRowDiv.append("div").attr("class", "col-md-12");

//Update initiates an OLI update
var updateButton = buttonDiv.append("input")
    .attr("type", "submit")
    .attr("value", "Update Layout")
    .attr("class", "btn btn-sm btn-default")
    .on("click", function() {
    	var numSelectedNodes = 0;
     	for (i = 0; i < nodes.length; i++) {
            if(nodes[i].selected==true) {
                numSelectedNodes++;
            }		
        }
     	
     	if(numSelectedNodes >= 3) {
            socket.emit("update", {type: "oli"});
            var i;
            for (i = 0; i < nodes.length; i++) {
                nodes[i].selected = false;
                nodes[i].moved = false;
                socket.emit('action', {type: "select", state: nodes[i].selected, id: nodes[i].id});
            }
            force.start();
        }
    });

// Reset button that resets the whole pipeline
var resetButton = buttonDiv.append("input")
    .attr("type", "submit")
    .attr("value", "Reset")
    .attr("class", "btn btn-sm btn-default")
    .on("click", function() {
        socket.emit("reset");
    });

d3.select("body").append("br");
var dataRow = d3.select("body").append("div").attr("class", "container-fluid");

//sets the canvas for nodes *looks normal in Google chrome, not with Internet Explorer
// Initialize SVG
var svgCol = dataRow.append("div").attr("class", "col-md-8");


var svg = svgCol.append("svg")
    // Set SVG width to 100% of column width
    .style("width", "100%")
    // Set SVG height to equal column width for data label
    .style("height", function() {
        width = this.clientWidth;
        height = width * 0.6;
        return height;
    })
    .on('click', function() {
        if (d3.event.target == this) {
            dispatch.unhighlightAll();
            updateIndicators();
        }

        d3.selectAll('.selected').classed('selected', function(d) {
            updateIndicators();
        });
    })
    .on("contextmenu", function() {
        d3.event.preventDefault();
    });


// Initialize force layout
var force = d3.layout.force()
    .gravity(0)
    .friction(0)
    .charge(0)
    .nodes(nodes);


// Catch the drag events
var drag = force.drag()
    .on("dragstart", dragstart)
    .on("drag", dragmove)
    .on("dragend", dragend);


var dispatch = d3.dispatch('unhighlightAll', 'toggle')
    .on('unhighlightAll', function() {
        //d3.selectAll('.selected').classed('selected', false);
        for (var i = 0; i < nodes.length; i++) {
           nodes[i].selected = false;
           socket.emit('action', 
                       {
                        type: "select",
                        state: nodes[i].selected,
                        id: nodes[i].id
            });
        }
        force.start();
        d3.selectAll('.selected').classed('selected', false);
    })
    .on('toggle', function(d) {
        d3.select(d).classed('selected', function() {
            updateIndicators();
            return !d3.select(d).classed('selected');
        });
        updateIndicators();
    });

// Initialize force layout actions
var node = svg.selectAll(".node").data(nodes);
updateLayout();

//Slider
var dataContents = dataRow.append("div").attr("class", "col-md-4").style("height", height + "px").style("width", 308 + "px")
var svg2 = dataContents.append("svg").attr("id", "dataContents");
/*
svg.append("rect")
    .attr("class", "button")
    .attr("rx", 3)
    .attr("ry", 3)
    .attr("width", 105)
    .attr("height", 30)
    .attr("y", 0)
    .attr("x", 2)
    .on('mouseover', function(d) {
        tempColor = this.style.fill;
        d3.select(this)
            .style('fill', '#C5CAE9')
            .style('opacity', .8)

    })

.on('mouseout', function(d) {
    d3.select(this)
        .style('opacity', 1)
        .style('fill', tempColor)
});
*/

var width = 175;
var height = 120;
var dummy = 0;

var slider = svg2.selectAll(".slider").data(sliders);

var x = d3.scale.linear()
    .domain([0, 1])
    .range([15, width])
    .clamp(true);
var x2 = d3.scale.linear()
    .domain([0, 1])
    .range([.33, 1])
    .clamp(true);
updateSlider();


// Function when force layout updates
// Updates points on screen and smoothly transitions them to their new location
force.on("tick", function() {
    var movingNode = null;
    for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].moving) {
            movingNode = nodes[i];
            break;
        }
    }
    if (movingNode) {
        for (var i = 0; i < nodes.length; i++) {
            if (movingNode == nodes[i]) {
                continue;
            }

            var distanceX = Math.pow((movingNode.X - nodes[i].X), 2);
            var distanceY = Math.pow((movingNode.Y - nodes[i].Y), 2);
            var distanceXY = Math.sqrt(distanceX + distanceY);

            if (distanceXY < outerRadius) {
                nodes[i].movingSelected = true;
                getAttributes(nodes[i]);
            }
            else {
                nodes[i].movingSelected = false;
            }
        }
    }

    node.attr("transform", function(d) {
            return "translate(" + d.X + "," + d.Y + ")";
        })
        .classed("selected", function(d) {
            return d.selected;
        })
        .classed("moving", function(d) {
            return d.moving;
        })
        .classed("indicate", function(d) {
            return d.indicate;
        })
        .classed("moving-selected", function(d) {
            return d.movingSelected;
        })
        .classed("hover", function(d) {
            return d.hover;
        });
    
    updateIndicators();
    force.stop();
});


function updateLayout() {
    // Give data to SVG
    node = node.data(nodes, function(d) {
        return d.id;
    });

    // Remove any documents that no longer exist
    node.exit().remove();

    // Create the group node who's transform servers as the position of the
    // node and have new nodes come in from (0, 0)

    var g = node.enter().append("g")
        .attr("class", "node")
        .classed("selected", function(d) {
            return d.selected;
        })
        .on('mouseover', function(d) {
            if (!d3.select(".moving")[0][0]) {
                d.hover = true;
                getAttributes(d);
                force.start();
            }
        })
        .on('mouseout', function(d) {
            if (!d3.select(".moving")[0][0]) {
                d.hover = false;
                force.start();
            }
        })
        .on("click", function(d) {
            d3.select(".selected")
                .classed('selected', true);
            getAttributes(d);
            updateIndicators();
        })
        .call(drag);

    //adds pattern to node
    var pattern = g.append("pattern")
        .attr({
            id: "stripe_me",
            width: "6",
            height: "6",
            patternUnits: "userSpaceOnUse",
            patternTransform: "rotate(-45)"
        })
        .append("rect")
        .attr({
            width: "4",
            height: "8",
            transform: "translate(0,0)",
            fill: "#FFFF00"
        });

    var pattern2 = g.append("pattern")
        .attr({
            id: "stripe_me2",
            width: "6",
            height: "6",
            patternUnits: "userSpaceOnUse",
            patternTransform: "rotate(-45)"
        })
        .append("rect")
        .attr({
            width: "4",
            height: "8",
            transform: "translate(0,0)",
            fill: "#D500F9"
        });

    var pattern3 = g.append("pattern")
        .attr({
            id: "stripe_me3",
            width: "6",
            height: "6",
            patternUnits: "userSpaceOnUse",
            patternTransform: "rotate(-45)"
        })
        .append("rect")
        .attr({
            width: "4",
            height: "8",
            transform: "translate(0,0)",
            fill: "#1DE9B6"
        });
        
    // Add a circle for the point of the node on initial load out
    g.append("circle")
        .attr("class", "point")
        .attr("r", radius + 30)
        .attr("id", "inner")
        .append("title").text(function(d) {
            return d.label;
        });
        
    g.append("circle")
        .attr("class", "outer")
        .attr("cx", -2)
        .attr("cy", 0)
        .attr("r", outerRadius);

    // Add a label for the point to the right
    g.append("text")
        .attr("class", "text")
        .attr("dx", 10)
        .attr("dy", ".35em")
        .text(function(d) {
            return d.label;
        })
        .style("stroke", function(d) {
            if (!d.selected || !d.movingSelected) {
                d3.select(this)
                    .classed("chosen", true);
            }
        });

    // Select/deselect node on click
    g.on("click", function(d) {
        if (!d.selected || !d.movingSelected) {
            d3.select(this)
                .classed("highlighted", true);
                updateIndicators();
        }
    });

    // Force layout running screws up the transition
    force.stop();

    // Transition the nodes to their new positions
    node.transition().ease("linear").duration(1000)
        .attrTween("transform", function(d, i, a) {
            return d3.interpolateTransform(a, "translate(" + d.X + "," + d.Y + ")");
        });

    // Transition each node to it's new size based on it's relevance and is what sets the size of each 
    //node when seen initially

    d3.selectAll("circle.point").transition().ease("linear").duration(1000)
        .attr("r", function(d) {
            return 8 + 10 * d.relevance;
        });
}

function updateSlider() {
	node.classed("selected", false);
	node.classed("selected", function(d) {
            d.selected = false;
            socket.emit('action', { type: "select", state: d.selected, id: d.id });
        });
	
    slider = slider.data(sliders, function(d) {
        return d.id;
    });

    slider.exit().remove();

    var g = slider.enter().append("g")
        .attr("class", "slider")
        .attr("transform", function(d) {
            return "translate(0," + (d.order + 1) * 25 + ")"
        });

    g.append("line")
        .attr("class", "track")
        .attr("x1", x.range()[0])
        .attr("x2", x(x2(0)))
        .select(function() {
            return this.parentNode.appendChild(this.cloneNode(true));
        })
        .attr("class", "halo");

    g.append("line")
        .attr("class", "zero")
        .attr("x1", x(x2(0)))
        .attr("x2", x(x2(0)))
        .attr("y1", -10)
        .attr("y2", 10);

    var handle = g.append("circle")
        .attr("class", "handle")
        .attr("r", 9)
        .attr('cx', x(x2(0)))
        .on('mouseover', function(d) {
            tempColor = this.style.fill;
            d3.select(this)
                .style('fill', '#C5CAE9')
        })
        .on('mouseout', function(d) {
            d3.select(this)
                .style('opacity', 1)
                .style('fill', tempColor)
        })
        .call(d3.behavior.drag()
            .on("dragstart", function() {

            })
            .on("drag", function() {
                d3.select(this)
                    .attr("cx", x(x.invert(d3.event.x)));
            })
            .on("dragend", function(d) {
                var value = x2.invert(x.invert(d3.select(this)
                    .attr("cx")));
                socket.emit("update", {
                    type: "pi",
                    param: d.id,
                    value: value

                });
            }));

    g.append("text")
        .attr("class", "text")
        .attr("dx", 190)
        .attr("dy", ".33em")
        .text(function(d) {
            return d.id;
        })
        .style("stroke", "gray");

    // Transition the nodes to their new positions
    slider.transition().ease("linear").duration(1000)
        .attrTween("transform", function(d, i, a) {
            return d3.interpolateTransform(a, "translate(0," + (d.order + 1) * 25 + ")");
        });

    slider.selectAll(".track, .halo").transition().ease("linear").duration(1000)
         .attr("x2", function(d) {
             return x(x2(d.weight));
        });

    slider.select(".handle").transition().ease("linear").duration(1000)
        .attr("cx", function(d) {
            return x(x2(d.weight));
        });
}


function getAttributes(d) {
	if (!d.attributes) {
        socket.emit("get", {
            type: "attributes",
            id: d.id
        });
    }
}


function updateIndicators() {
    var nameStuff = {};
    
    var highlight = d3.selectAll('.selected').select(function(d) {
    	if (d.hover) {
            return;
        }
    	
        if (d.attributes) {
            for (var attr in d.attributes) {
            	if (!nameStuff[attr]) {
                    nameStuff[attr] = [];
                }

                var obj = {};
                obj.id = d.id;
                obj.value = d.attributes[attr];
                obj.highlighted = true;

                nameStuff[attr].push(obj);
            }
        }
        else {
            getAttributes(d);
        }
    });

    d3.select('.hover').select(function(d) {
        if (d.attributes) {
            for (var attr2 in d.attributes) {
                if (!nameStuff[attr2]) {
                    nameStuff[attr2] = [];
                }
                var obj2 = {};
                obj2.id = d.id;
                obj2.value = d.attributes[attr2];
                obj2.chosen = true;

                nameStuff[attr2].push(obj2);
            }
        }
        else {
            getAttributes(d);
        }
    });
    
    slider.select(function(d) {
        if (!nameStuff[d.id]) {
            d.indicator = d3.select(this).select(".indicator").data([], function(d) {
                return "";
            });
            d.indicator.exit().remove();
        }
        else {
            d.indicator = d3.select(this).selectAll(".indicator").data(nameStuff[d.id], function(d) {
                return d.id;
            });

            d.indicator.exit().remove();

            d.indicator.enter().append("circle")
                .attr("class", "indicator")
                .attr("r", 4.5)
                .attr("cx", function(d2) {
                    return x(x2(d.weight) * d2.value);
                });
                
            d.indicator
                .classed("highlighted", function(d) {
                    return d.highlighted;
                })
                .classed("chosen", function(d) {
                    return d.chosen;
                });
            
            // Make sure the chosen indicator is always on top
            d.indicator.select(function(d) {
            	if (d.chosen) {
            		this.parentNode.appendChild(this);
            	}
            });
        }
        /*
        b.on("mouseover", function(d) {
            d3.select(this)
                .classed('selected', true)
                .append("text").style("pointer-events", "none")
                .attr("class", "text")
                .attr("dx", 10)
                .attr("dy", "-1em")
                .text(function(d) {
                    return d.id;
                })
                .attr("transform", function(d) {
                    return "translate(" + (d.value) + ")"
                })
                .style("stroke", "gray")

        })

        .on("mouseout", function(d) {

            d3.select(this).select("text").remove();

        });
        */
    });

    slider.select(function(d) {
        if (d.indicator) {
            d.indicator.transition().ease("linear").duration(1000)
                .attr("cx", function(d2) {;
                    return x(x2(d.weight) * d2.value);
                });
        }
    });
}


function update(data) {
    /* Update format:
     * points: [
     *  {
     *  id: <string>,
     *  label: <string>,
     *  pos: [],
     *  selected: <boolean>,
     *  relevance: <float [0, 1]>
     * }
     */
    if (data.points) {
        for (var i = 0; i < data.points.length; i++) {
            var point = data.points[i];
            var id = point.id;
            var pos = null;
            if (point.pos) {
                pos = {};
                width = Number(svg.style("width").replace("px", ""));
                height = Number(svg.style("height").replace("px", ""));
                
                // Each dimension is in [-1, 1]. We need to translate
                // this into x and y coordinates to map the points into
                // the svg. Additionally, we should make sure that we
                // project into a square area so that we don't
                // distort the projection by stretching it in any
                // direction
                // We start by determining whether the width or height
                // of the svg is smaller to start making our square
                var size;
                var xShift;
                var yshift;
                if (width < height) {
                    size = width;
                    xShift = 0;
                    yshift = (height-width)/2.0;
                }
                else {
                    size = height;
                    xShift = (width-height)/2.0;
                    yshift = 0;
                }
                
                // Now that we know how to map our points onto the
                // square, we should project them. However, we should
                // only use 90% of the space so that points don't lie
                // on the svg boundaries
                var usableScale = 0.9;
                var unusableScaleSize = (1-usableScale)*size;
                var scaleSize = usableScale*size;
                
                // Do the final x- and y-coordinate calculations
                pos.x = (point.pos[0] + 1) / 2.0 * scaleSize + unusableScaleSize/2 + xShift;
                pos.y = (-point.pos[1] + 1) / 2.0 * scaleSize + unusableScaleSize/2 + yshift;
            }

            // Very inefficient, use a Map instead
            for (var j = 0; j < nodes.length; j++) {
                if (nodes[j].id === id) {
                    // Found node, update it
                    if (pos) {
                        // We got a new position, so update the position
                        nodes[j].X = pos.x;
                        nodes[j].Y = pos.y;
                    }
                    
                    // Update the relevance if we received it
                    if ("relevance" in point) {
                        nodes[j].relevance = point.relevance;
                    }
                    
                    // Update the selected status if we received it
                    if ("selected" in point) {
                        nodes[j].selected = point.selected;
                    }
                    
                    // Let the point be deselected
                    nodes[j].moved = false;
                    break;
                }
            }

            // If the point wasn't found, create and add it
            if (j === nodes.length) {
                var label = "";
                if (point.type === "attribute") {
                    label = attributes[parseInt(point.id)];
                }
                else {
                    label = point.label || point.id;
                }
                
                var newNode = {
                    id: point.id,
                    label: label,
                    type: point.type || "News",
                    X: pos.x,
                    Y: pos.y,
                    selected: point.selected,
                    relevance: point.relevance || 0,
                    notes: ""
                };
                nodes.push(newNode);
            }
        }
        updateLayout();
    }
    if (data.similarity_weights) {
        /*id: "Final Fantasy 4",
            
            weight: 0.5,
            order: 0,
        
            values: []*/
        for (var i = 0; i < data.similarity_weights.length; i++) {
            var attribute = data.similarity_weights[i];

            for (var j = 0; j < sliders.length; j++) {
                if (sliders[j].id === attribute.id) {
                    sliders[j].weight = attribute.weight;
                    break;
                }
            }

            if (j === sliders.length) {
                var obj = {};
                obj.id = attribute.id;
                obj.weight = attribute.weight;
                obj.values = [];

                sliders.push(obj);
            }
        }
        
        sliders.sort(function(a, b) {
        	if (a.weight < b.weight) {
                    return 1;
                }
        	else if (a.weight > b.weight) {
                    return -1;
                }
        	else if (a.id < b.id) {
                    return -1;
                }
        	else if (a.id > b.id) {
                    return 1;
                }
        	else {
                    return 0;
                }
        });
        
        for (var i = 0; i < sliders.length; i++) {
            sliders[i].order = i;
        }

        updateSlider();
        updateIndicators();
    }
}


// What to do when a node is clicked
function dragstart(d, i) {
    // Select or deselect the node
    // d.selected = d.moved || !d.selected;

    var old = d.selected;

    // Toggle the selected status, unless the node has been moved
    d.selected = !d.selected || (d3.event.sourceEvent.button === 0 && d.moved);
    if (d.selected != old) {
        // If the selected status has changed, broadcast it and update the
        // layout.
        socket.emit('action', {
            type: "select",
            state: d.selected,
            id: d.id
        });
        force.start();
    }
}


// What to do when a node is dragged
function dragmove(d) {
    // Update the node's properties to reflect the dragging action

    // Make sure this point stays selected until the layout is updated
    d.moved = true;
    d.moving = true;
  
    getAttributes(d);
    
    if (!d.selected) {
        // If the point wasn't selected, select it and broadcast it
        d.selected = true;
        socket.emit('action', {
            type: "select",
            state: d.selected,
            id: d.id
        });
        force.start();
    }
    
    d.X += d3.event.dx;
    d.Y += d3.event.dy;
    
    // Broadcast the moved event
    socket.emit('action', {
        type: "move",
        pos: [d.X / width * 2 - 1, -(d.Y / height * 2 - 1)],
        id: d.id
    });
}


// What to do when a dragged node is released
function dragend(d, i) {
    // Make sure the layout updates properly
    d.moving = false;
    for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].movingSelected) {
            nodes[i].selected = true;
            socket.emit('action', 
         	{
                 type: "select",
                 state: nodes[i].selected,
                 id: nodes[i].id
             });
        }
        nodes[i].movingSelected = false;
    }
    force.start();
}



var socket = io.connect({reconnection:false});

function createUISocketCallbacks() {
    socket.on('connect', function() {
    });


    socket.on('disconnect', function() {
    });


    socket.on('action', function(data) {
        if (data.type === "move") {
            /* Data format:
             * id: <string>,
             * pos: [] (each [0, 1])
             */
            var x = (data.pos[0] + 1) / 2 * width;
            var y = (-data.pos[1] + 1) / 2 * height;
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id === data.id) {
                    // Found node, update it
                    nodes[i].X = x;
                    nodes[i].Y = y;

                    break;
                }
            }
            force.start();
        }
        else if (data.type === "select") {
            /* Data format:
             * id: <string>,
             * state: <boolean>
             */
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id === data.id) {
                    nodes[i].selected = data.state;
                }
            }
            force.start();
        }
    });


    socket.on('update', function(data) {
        update(data);
    });


    socket.on('get', function(data) {
        if (!data || !data.type) {
            return;
        }

        if (data.type === "attributes" && data.id) {
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id === data.id) {
                    nodes[i].attributes = data.value;
                    updateIndicators();
                    break;
                }
            }
        }
        else if (data.type === "raw") {
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id === data.id) {
                    nodes[i].content = data.value;
                    break;
                }
            }
            updateDataPanel();
        }
    });


    socket.on('reset', function() {
        nodes.length = 0;
        sliders.length = 0;
        updateLayout();
        updateSlider();
        updateIndicators();
    });

    socket.emit('get', {
        type: 'attributes'
    });
}
