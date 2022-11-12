var ui = "andromeda";
var nodes = [];
var sliders = [];
var hovered_attr = null;

// A variable to help track when a node has just been moved
var justMovedNode = false;

//==========================================================
//Buttons
//==========================================================
//Update initiates an OLI update
var updateButton = d3.select("#update")
    .on("click", function () {
        var numSelectedNodes = 0;
        for (i = 0; i < nodes.length; i++) {
            if (nodes[i].selected == true) {
                numSelectedNodes++;
            }
        }

        if (numSelectedNodes >= 3) {
            socket.emit("update", { type: "oli" });
            var i;
            for (i = 0; i < nodes.length; i++) {
                nodes[i].selected = false;
                nodes[i].moved = false;
                socket.emit('action', { type: "select", state: nodes[i].selected, id: nodes[i].id });
            }
            dispatch.unhighlightAll();
            force.start();
        }
    });


// Reset button that resets the whole pipeline
var resetButton = d3.select("#reset")
    .on("click", function () {
        socket.emit("reset");
    });


// Information button
var infoButton = d3.select("#info")
    .on("click", function () { });



// ZoomIn and ZoomOut Button






//==========================================================
//OLI
//==========================================================
var oli = d3.select("#oli");
//.on("contextmenu", function() {
//d3.event.preventDefault();
//})
//    .on("click", function() {
//        if (d3.event.target == this) {
//            dispatch.unhighlightAll();
//        }
//    });
var oliDiv = d3.select("div#oliDiv");

// Dynamically determine the height of the OLI panel
oliDiv.style("height", function () {
    var totalHeight = Number(String(d3.select("html").node().clientHeight).replace("px", ""));
    var topRowHeight = Number(d3.select("div#topRow").style("height").replace("px", ""));
    var oliDivMargins = Number(oliDiv.style("margin-top").replace("px", "")) +
        Number(oliDiv.style("margin-bottom").replace("px", "")) * 2;
    var oliDivHeight = totalHeight - topRowHeight - oliDivMargins;
    return oliDivHeight + "px";
});

d3.select("div#groups")
    // If we want the Groups panel
    //        .style("height", "150px")
    //        .style("padding-top", "10px");

    // If we don't want the Groups panel
    .remove();


d3.select("div#attributes")
    // Dynamically determine the height of the attribute div
    .style("height", function () {
        // Initially, make the attribute div height equal to the
        // OLI div
        var attrDivHeight = Number(oliDiv.style("height").replace("px", ""));

        // If the groups panel is displayed, subtract the height of it from
        // the height of the OLI div
        var groupsDiv = d3.select("div#groups");
        if (groupsDiv.node()) {
            var groupsDivHeight = Number(groupsDiv.style("height").replace("px", ""));
            var groupsDivMargins = Number(groupsDiv.style("margin-top").replace("px", "")) +
                Number(groupsDiv.style("margin-bottom").replace("px", ""));
            attrDivHeight -= groupsDivHeight + groupsDivMargins;
        }

        // Set the height of the attribute div
        return attrDivHeight + "px";
    })
    // Dynamically determine the height of the attribute scrolling div
    .select("div").style("height", function () {
        // Get the height of the OLI panel
        var totalHeight = Number(oliDiv.style("height").replace("px", ""));

        // Get the height of the groups panel, if it exists
        var groupsHeight = 0;
        var groupsDiv = d3.select("div#groups");
        if (groupsDiv.node()) {
            var groupsDivHeight = Number(groupsDiv.style("height").replace("px", ""));
            var groupsDivMargins = Number(groupsDiv.style("margin-top").replace("px", "")) +
                Number(groupsDiv.style("margin-bottom").replace("px", ""));
            groupsHeight = groupsDivHeight + groupsDivMargins;
        }

        // Get the height of the header components of the attribute panel
        var attributeDiv = d3.select(this.parentNode);
        var header = attributeDiv.select("p");
        var headerHeight = Number(header.style("line-height").replace("px", ""));
        var headerMargin = Number(header.style("margin-top").replace("px", "")) +
            Number(header.style("margin-bottom").replace("px", ""));
        var attributeDivMargin = Number(d3.select(this).style("margin-bottom").replace("px", ""));

        // Calculate and return what the height of the attribute panel
        // should be
        var attributeListDivHeight = totalHeight - headerHeight -
            headerMargin - attributeDivMargin - groupsHeight;
        return attributeListDivHeight + "px";
    });


//==========================================================
//Force layout and drag
//==========================================================
var force = d3.layout.force()
    .gravity(0)
    .friction(0)
    .charge(0)
    .nodes(nodes);


//Create the drag and drop behavior
var drag = force.drag()
    .on("dragstart", dragstart)
    .on("drag", dragmove)
    .on("dragend", dragend);


//what to do when a node is clicked
function dragstart(d, i) {
    force.start();
}

//what to do when a node is dragged
function dragmove(d, i) {
    if (!d.selected) {
        // If the point wasn't selected, select it and broadcast it
        d.selected = true;
        socket.emit('action', { type: "select", state: d.selected, id: d.id });

        // Call the force.start() function to update the view
        d3.select(this).classed("selected", function (d) { return d.selected; });
    }

    // Track the movement of the node
    d.moved = true;
    d.moving = true;
    justMovedNode = true;

    d.X += d3.event.dx;
    d.Y += d3.event.dy;
    d3.select(this).attr("transform", function (d) {
        return "translate(" + d.X + "," + d.Y + ")";
    });


    // Broadcast the moved event
    socket.emit('action', {
        type: "move",
        pos: [d.X / width * 2 - 1, -(d.Y / height * 2 - 1)],
        id: d.id
    });
}

//what to do when a node is released
function dragend(d, i) {
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



var dispatch = d3.dispatch('unhighlightAll', 'toggle')
    .on('unhighlightAll', function () {
        for (var i = 0; i < nodes.length; i++) {
            nodes[i].selected = false;
            socket.emit('action',
                {
                    type: "select",
                    state: nodes[i].selected,
                    id: nodes[i].id
                });
        }
        d3.selectAll('.selected').classed('selected', false);
        updateIndicators();
    })
    .on('toggle', function (d) {
        d3.select(d).classed('selected', function () {
            return !d3.select(d).classed('selected');
        });
        updateIndicators();
    });


// Initialize force layout actions
var node = oli.selectAll(".node").data(nodes);

//Slider
var svg2 = d3.select("#pi");

var width = 175;

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


// Updates points on screen and smoothly transitions them to their new location
force.on("tick", function () {
    node.attr("transform", function (d) {
        return "translate(" + d.X + "," + d.Y + ")";
    })
        .classed("selected", function (d) {
            return d.selected;
        })
        .classed("moving", function (d) {
            return d.moving;
        })
        .classed("indicate", function (d) {
            return d.indicate;
        })
        .classed("moving-selected", function (d) {
            return d.movingSelected;
        })
        .classed("hover", function (d) {
            return d.hover;
        });

    updateIndicators();
    force.stop();
});


function updateLayout() {


    // Give data to SVG
    node = node.data(nodes, function (d) {
        return d.id;
    });

    // Remove any documents that no longer exist
    node.exit().remove();

    // Create the group node who's transform servers as the position of the
    // node and have new nodes come in from (0, 0)
    var g = node.enter().append("g")
        .attr("class", "node")
        .on('mouseover', function (d) {
            if (!d3.select(".moving")[0][0]) {
                d.hover = true;
                getAttributes(d);
                force.start();
            }
        })
        .on('mouseout', function (d) {
            if (!d3.select(".moving")[0][0]) {
                d.hover = false;
                force.start();
            }
        })
        //        .on("click", function(d) {
        //            d3.select(".selected")
        //                .classed('selected', true);
        //            getAttributes(d);
        //            updateIndicators();
        //        })
        .call(drag);

    // Add a circle for the point of the node on initial load out
    g.append("circle")
        .attr("class", "point")
        .attr("id", "inner")
        .append("title").text(function (d) {
            return d.label;
        });

    // Add a label for the point to the right
    g.append("text")
        .attr("class", "text")
        .attr("dx", 10)
        .attr("dy", ".35em")
        .text(function (d) {
            return d.label;
        })
        .style("stroke", function (d) {
            if (!d.selected || !d.movingSelected) {
                d3.select(this)
                    .classed("chosen", true);
            }
        });

    // Select/deselect node on click
    g.on("click", function (d) {
        if (d.type !== "attribute-v") {
            // If we just moved a node, prevent a "click" action from being
            // registered. (2 click actions are registered for every drag.)
            if (!justMovedNode) {
                d.selected = !d.selected;
                d3.select(this).classed("selected", function (d) { return d.selected; });
                socket.emit('action', { type: "select", state: d.selected, id: d.id });

                getAttributes(d);
                updateIndicators();
            }
            else {
                justMovedNode = false;
            }
        }
    });

    // Force layout running screws up the transition
    force.stop();

    // Transition the nodes to their new positions
    node.transition().ease("linear").duration(1000)
        .attrTween("transform", function (d, i, a) {
            return d3.interpolateTransform(a, "translate(" + d.X + "," + d.Y + ")");
        });

    // Transition each node to it's new size based on it's relevance and is what sets the size of each 
    // node when seen initially

    node.selectAll("circle").transition().ease("linear").duration(1000)
        .attr("r", function (d) {
            return 8 + 5 * d.relevance;
        })
        .attr("opacity", function (d) {
            var relevance = d.relevance;
            var opacityRange = 0.6;
            return opacityRange * Math.log((relevance + 0.1) / 0.1) / Math.log(1.1 / 0.1) + (1 - opacityRange / 1.25) - 0.2;
        })
        .style("stroke", function (d) {
            if (hovered_attr) {
                return "purple";
            }
            else {
                return null;
            }
        })
        .style("stroke-width", function (d) {
            if (hovered_attr) {
                return 10 * d.attributes[hovered_attr];
            }
            else {
                return null;
            }
        });
}


function updateSlider() {
    node.classed("selected", false);
    node.classed("selected", function (d) {
        d.selected = false;
        socket.emit('action', { type: "select", state: d.selected, id: d.id });
    });

    slider = slider.data(sliders, function (d) {
        return d.id;
    });

    slider.exit().remove();

    var g = slider.enter().append("g")
        .attr("class", "slider")
        .attr("transform", function (d) {
            return "translate(0," + (d.order + 1) * 25 + ")"
        });

    g.append("line")
        .attr("class", "track")
        .attr("x1", x.range()[0])
        .attr("x2", x(x2(0)))
        .select(function () {
            return this.parentNode.appendChild(this.cloneNode(true));
        })
        .attr("class", "halo");

    g.append("line")
        .attr("class", "zero")
        .attr("x1", x(x2(0)))
        .attr("x2", x(x2(0)))
        .attr("y1", -10)
        .attr("y2", 10);

    //==============bind text with pi circle handle=========================
    var handle = g.append("g")
        .call(d3.behavior.drag()
            .on("dragstart", function () {

            })
            .on("drag", function () {
                d3.select(this.children[0])
                    .attr("cx", x(x.invert(d3.event.x)));
                d3.select(this.children[1])
                    .attr("x", x(x.invert(d3.event.x)) + 15);
            })
            .on("dragend", function (d) {
                var value = x2.invert(x.invert(d3.select(this.children[0])
                    .attr("cx")));

                socket.emit("update", {
                    type: "pi",
                    param: d.id,
                    value: value

                });
                dispatch.unhighlightAll();
            }))
        .on("mouseover", function (d) {
            hovered_attr = d.id;
            updateLayout();
        })
        .on("mouseout", function () {
            hovered_attr = null;
            updateLayout();
        });

    handle.append("circle")
        .attr("class", "handle")
        .attr("r", 9)
        .on('mouseover', function (d) {
            tempColor = this.style.fill;
            d3.select(this)
                .style('fill', '#C5CAE9')
        })
        .on('mouseout', function (d) {
            d3.select(this)
                .style('opacity', 1)
                .style('fill', tempColor)
        })


    handle.append("text")
        .attr("class", "text")
        .attr('x', x(x2(0)) + 15)
        .attr("dy", ".33em")
        .text(function (d) {
            return d.id;
        })
        .style("stroke", "gray");
    //============================================

    // Transition the nodes to their new positions
    slider.transition().ease("linear").duration(1000)
        .attrTween("transform", function (d, i, a) {
            return d3.interpolateTransform(a, "translate(0," + (d.order + 1) * 25 + ")");
        });

    slider.selectAll(".track, .halo").transition().ease("linear").duration(1000)
        .attr("x2", function (d) {
            return x(x2(d.weight));
        });

    slider.select(".handle").transition().ease("linear").duration(1000)
        .attr("cx", function (d) {
            return x(x2(d.weight));
        });

    //text move with handle circle
    slider.select(".text").transition().ease("linear").duration(1000)
        .attr("x", function (d) {
            return x(x2(d.weight)) + 15;
        });

    //Resize svg
    if (sliders.length != 0) {
        var sliderArr = d3.selectAll(".slider")[0];
        var length = sliderArr.length;
        var lastSlider = sliderArr[length - 1];
        var transformVal = lastSlider.getAttribute("transform");
        var transformY = parseInt((transformVal.replace(/,/g, " ").split(" "))[1]);

        if (piheight != 0) {
            svg2.attr("height", piheight);
        }
        else {
            piheight = transformY + 15;
            svg2.attr("height", piheight);
        }
    }

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

    var highlight = d3.selectAll('.selected').select(function (d) {
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

    d3.select('.hover').select(function (d) {
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

    slider.select(function (d) {
        if (!nameStuff[d.id]) {
            d.indicator = d3.select(this).select(".indicator").data([], function (d) {
                return "";
            });
            d.indicator.exit().remove();
        }
        else {
            d.indicator = d3.select(this).selectAll(".indicator").data(nameStuff[d.id], function (d) {
                return d.id;
            });

            d.indicator.exit().remove();

            d.indicator.enter().append("circle")
                .attr("class", "indicator")
                .attr("r", 4.5)
                .attr("cx", function (d2) {
                    return x(x2(d.weight) * d2.value);
                })
                .append("title").text(function (i) {
                    return i.id + ": " + i.value;
                });

            d.indicator
                .classed("highlighted", function (d) {
                    return d.highlighted;
                })
                .classed("chosen", function (d) {
                    return d.chosen;
                });

            // Make sure the chosen indicator is always on top
            d.indicator.select(function (d) {
                if (d.chosen) {
                    this.parentNode.appendChild(this);
                }
            });
        }
    });

    slider.select(function (d) {
        if (d.indicator) {
            d.indicator.transition().ease("linear").duration(1000)
                .attr("cx", function (d2) {
                    ;
                    return x(x2(d.weight) * d2.value);
                });
        }
    });
}



function update(data) {
    if (data.similarity_weights) {
        /*id: "Final Fantasy 4",

            weight: 0.5,
            order: 0,

            values: []*/
        var tempSliders = []
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

                tempSliders.push(obj);
            }

            if (tempSliders.length === data.similarity_weights.length) {
                sliders.length = 0;
                sliders = tempSliders;
            }
            else {
                sliders.concat(tempSliders);
            }
        }

        sliders.sort(function (a, b) {
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
                width = Number(oli.style("width").replace("px", ""));
                height = Number(oli.style("height").replace("px", ""));

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
                    yshift = (height - width) / 2.0;
                }
                else {
                    size = height;
                    xShift = (width - height) / 2.0;
                    yshift = 0;
                }

                // Now that we know how to map our points onto the
                // square, we should project them. However, we should
                // only use 90% of the space so that points don't lie
                // on the svg boundaries
                var usableScale = 0.9;
                var unusableScaleSize = (1 - usableScale) * size;
                var scaleSize = usableScale * size;

                // Do the final x- and y-coordinate calculations
                pos.x = (point.pos[0] + 1) / 2.0 * scaleSize + unusableScaleSize / 2 + xShift;
                pos.y = (-point.pos[1] + 1) / 2.0 * scaleSize + unusableScaleSize / 2 + yshift;
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
        nodes.forEach(function (d) {
            getAttributes(d);
        });
        calculateRelevances();
        updateLayout();
    }
}

function calculateRelevances() {
    nodes.forEach(function (d) {
        if (d.attributes) {
            var relevance = 0;
            for (var i = 0; i < sliders.length; i++) {
                var attr_name = sliders[i].id;
                var weight = sliders[i].weight;
                var attr_relevance = d.attributes[attr_name] * weight;
                relevance += attr_relevance;
            }

            d.relevance = relevance;
        }
        else {
            d.relevance = 0;
        }
    });
}


var socket = io.connect({ reconnection: false });

function createUISocketCallbacks() {
    socket.on('connect', function () {
    });


    socket.on('disconnect', function () {
    });


    socket.on('action', function (data) {
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


    socket.on('update', function (data) {
        update(data);
    });


    socket.on('get', function (data) {
        if (!data || !data.type) {
            return;
        }

        if (data.type === "attributes" && data.id) {
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id === data.id) {
                    nodes[i].attributes = data.value;
                    updateIndicators();
                    calculateRelevances();
                    updateLayout();
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
        }
    });


    socket.on('reset', function () {
        nodes.length = 0;
        sliders.length = 0;
        piheight = 0;
        updateLayout();
        updateSlider();
        updateIndicators();
    });

    socket.emit('get', {
        type: 'attributes'
    });
}
