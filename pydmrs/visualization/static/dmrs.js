// The MIT License (MIT)
// 
// Demophin and d3.arcdiagram.js both use the same terms of the MIT license.
// 
// Demophin: Copyright (c) 2014 Michael Wayne Goodman
//   (see https://github.com/goodmami/demophin)
// 
// d3.arcdiagram.js: Copyright (c) 2015 Michael Wayne Goodman
//   (see https://github.com/goodmami/d3-arcdiagram)
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.


var maxWidth = 600,
    height = 300;

var level_dy = 25,  // vertical separation between edges
    edge_radius = 15, // rounded corner radius,
    edge_xoffset = 10, // outgoing edges aren't centered
    node_dx = 20;  // horizontal separation between nodes

var color = d3.scale.category20();


function dmrsDisplay(svgElem, graph) {
//  d3.json(url, function(error, graph) {
      // calculate source and target for links
      prepareGraph(graph);

      var tip = d3.select("#tooltip")
          .style("opacity", 0);

      var id = svgElem;
      var svg = d3.select(svgElem)
        .attr("height", ((graph.maxTopLevel - graph.maxBottomLevel + 3) * level_dy));
      var g = svg.append("svg:g")
          .attr("transform", "translate(0," + ((graph.maxTopLevel + 2) * level_dy) + ")");

      g.append("defs").append("marker")
          .attr("class", "linkend")
          .attr("id", "arrowhead")
          .attr("refX", 1) /*must be smarter way to calculate shift*/
          .attr("refY", 2)
          .attr("markerWidth", 5)
          .attr("markerHeight", 4)
          .attr("orient", "auto")
          .append("path")
              .attr("d", "M0,0 L1,2 L0,4 L5,2 Z"); //this is actual shape for arrowhead

      var x_pos = 10;
      var nodes = g.selectAll(".node").order()
          .data(graph.nodes)
        .enter().append("svg:g")
          .attr("class", "node")
          .each(function(d) {
            var vps = [];
            for (var key in d.varprops) {
              vps.push("<td>" + key + "</td><td>=</td><td>" + d.varprops[key] + "</td>");
            }
            d.tooltipText = "<table><tr>" + vps.join("</tr><tr>") + "</tr></table>";
          });
      nodes.append("svg:text")
          .attr("class", "nodeText")
          .text(function(d) {
            if (d.carg) {
              return d.pred + "(" + d.carg + ")";
            } else {
              return d.pred;
            }
          })
          .attr("x", function(d, i) {
              d.bbox = this.getBBox();
              halfLen = d.bbox.width / 2;
              x = x_pos + halfLen;
              x_pos = x + halfLen + node_dx;
              d.x = x;
              return x;
          })
          .attr("y", function(d) { return 0; })
          .attr("dy", function(d) { return d.bbox.height/5; });
      nodes.insert("svg:rect", "text")
          .attr("class", "nodeBox")
          .attr("x", function(d) { return d.x - (d.bbox.width / 2) - 2; })
          .attr("y", function(d) { return - (d.bbox.height / 2) - 2; })
          .attr("width", function(d) { return d.bbox.width + 4; })
          .attr("height", function(d) { return d.bbox.height + 4; })
          .attr("rx", 4)
          .attr("ry", 4);
      nodes.on("mouseover", function(d) {
              if (!graph.sticky) { d3.select(this).classed("selected", true) };
              updateHighlights(id);
              tip.html(d.tooltipText)
                .style("opacity", 0.8);
          })
          .on("mousemove", function(d) {
              tip.style("left", (d3.event.pageX - 10) + "px")
                .style("top", (d3.event.pageY + 15) + "px");
          })
          .on("mouseout", function(d) {
              if (!d.sticky) { d3.select(this).classed("selected", false); }
              updateHighlights(id);
              tip.style("opacity", 0);
          })
          .on("click", function(d) {
              stickyState = toggleSticky(id, this, d);
              graph.sticky = stickyState;
              updateHighlights(id);
          });

      // not working...
      svg.attr("width", d3.sum(nodes.data(), function(d) { return d.bbox.width + node_dx; }));

      var links = g.selectAll(".link").order()
          .data(graph.links)
        .enter().append("svg:g")
          .attr("class", "link");
      links.append("svg:path")
          .attr("class", function(d) {
              if (d.start == 0) {
                  return "topedge";
              } else if (d.rargname == "" && d.post == "EQ") {
                  return "eqedge";
              } else {
                  return "linkedge";
              }
          })
          .attr("d", function(d) {
              return getPathSpec(d, graph);
          })
          .attr("transform", function(d) {
              return "scale(1," + (d.dir * -1) + ")";
          })
          .style("marker-end", function(d) {
              return (d.rargname == "" && d.post == "EQ") ? "none" : "url(#arrowhead)";
          });
      links.append("svg:text")
          .attr("class", "rargname")
          .attr("x", function(d) { return d.midpoint.x; })
          .attr("y", function(d) { return d.midpoint.y * (-1 * d.dir) - 3; })
          .text(function(d) { return d.rargname + "/" + d.post; } );
//  });
}


function prepareGraph(graph) {
    var nodeIdx = {}, levelIdx = {};
    graph.nodes.forEach(function(d, i) {
        nodeIdx[d.id] = i;
        levelIdx[[i,i+1].join()] = {}; // eg levelIdx["1,2"] = {}
    });
    graph.links.forEach(function(d) {
        d.target = nodeIdx[d.end];
        // start of 0 is TOP link
        if (d.start == 0) {
            d.dir = 1;  // always on top
            return;
        }
        // the rest only apply to non-TOP links
        d.source = nodeIdx[d.start];
        d.distance = Math.abs(d.source - d.target);
        // Quantifiers and undirected EQ links below preds
        d.dir = (d.rargname == "" || d.post.toUpperCase() == "H") ? -1 : 1
    });
    graph.maxTopLevel = 0;
    graph.maxBottomLevel = 0;
    for (dist=0; dist<graph.nodes.length; dist++) {
        graph.links.forEach(function(d) {
            if (d.start == 0) return;
            if (dist != d.distance) return;
            d.level = nextAvailableLevel(d.source, d.target, d.dir, levelIdx);
            if (d.dir == 1 && graph.maxTopLevel < d.level) {
                graph.maxTopLevel = d.level;
            } else if (d.dir == -1 && graph.maxBottomLevel > d.level) {
                graph.maxBottomLevel = d.level;
            }
        });
    }
    graph.sticky = false;
}


function nextAvailableLevel(source, target, dir, lvlIdx) {
    var level, curLevel, success;
    if (source > target)
        return nextAvailableLevel(target, source, dir, lvlIdx);
    level = 0;
    curLevel = dir;
    while (level == 0) {
        success = true;
        for (var i = source; i < target; i++) {
            if (curLevel in lvlIdx[[i, i+1].join()]) {
                success = false;
                break;
            }
        }
        if (success) {
            level = curLevel;
            for (var i = source; i < target; i++) {
                lvlIdx[[i, i+1].join()][level] = true;
            }
        } else {
            curLevel += dir;
        }
    }
    return level;
}


function getPathSpec(link, graph) {
    var x1, x2, y1, y2;
    // get these first, they apply for all links
    x2 = graph.nodes[link.target].x;
    y1 = graph.nodes[link.target].bbox.height;
    if (link.start == 0) {
        y2 = y1 + (((link.dir == 1 ? graph.maxTopLevel : graph.maxBottomLevel) + 1) * level_dy);
        link.midpoint = {"x": x2,
                         "y": (y1 + y2) / 2};
        return ["M", x2, y2, "L", x2, y1].join(' ');
    }
    // the following is only for non-TOP links
    x1 = graph.nodes[link.source].x;
    y2 = y1 + (Math.abs(link.level) * level_dy - 5);
    // side-effect! calculate this while we know it
    link.midpoint = {"x": (x1 + x2) / 2,
                     "y": y2};
    if (x1 < x2) {
        x1 += edge_xoffset;
        return ["M", x1, y1 - 5,
                "L", x1, (y2 - edge_radius),
                "Q", x1, y2, (x1 + edge_radius), y2,
                "L", (x2 - edge_radius), y2,
                "Q", x2, y2, x2, y2 - edge_radius,
                "L", x2, y1].join(' ');
    } else {
        x1 -= edge_xoffset;
        return ["M", x1, y1 - 5,
                "L", x1, (y2 - edge_radius),
                "Q", x1, y2, (x1 - edge_radius), y2,
                "L", (x2 + edge_radius), y2,
                "Q", x2, y2, x2, y2 - edge_radius,
                "L", x2, y1].join(' ');
    }
}


function updateHighlights(id) {
    clearHighlights(id);
    d3.select(id).selectAll(".node.selected").each(function(d){
        var labelset = d3.set(),
            outs = d3.set(),
            ins = d3.set(),
            scopes = d3.set();
        d3.select(id).selectAll(".link")
            .classed({
                "out": function(_d) {
                    if (_d.rargname && d.id == _d.start) {
                        outs.add(_d.end);
                        return true;
                    }
                    return false;
                },
                "in": function(_d) {
                    if (_d.rargname && d.id == _d.end) {
                        ins.add(_d.start);
                        return true;
                    }
                    return false;
                },
                "labelset": function(_d) {
                    if (_d.post == "EQ" && (_d.start == d.id || _d.end == d.id)) {
                        labelset.add(_d.start);
                        labelset.add(_d.end);
                        return true;
                    }
                    return false
                },
                "scope": function(_d) {
                    if (_d.start == d.id && (_d.post == "H" || _d.post == "HEQ")) {
                        scopes.add(_d.end);
                        return true;
                    } else if (_d.end == d.id && (_d.post == "H" || _d.post == "HEQ")) {
                        return true;
                    }
                    return false;
                }
            });
        var labelAdded = true;
        while (labelAdded) {
            labelAdded = false;
            d3.select(id).selectAll(".link").each(function(_d) {
                if (_d.post == "EQ") {
                    if (labelset.has(_d.start) && !labelset.has(_d.end)) {
                        labelset.add(_d.end);
                        labelAdded = true;
                    } else if (labelset.has(_d.end) && !labelset.has(_d.start)) {
                        labelset.add(_d.start);
                        labelAdded = true;
                    }
                }
            });
        }
        d3.select(id).selectAll(".node")
            .classed({
                "out": function(_d) { return outs.has(_d.id); },
                "in": function(_d) { return ins.has(_d.id); },
                "labelset": function(_d) { return labelset.has(_d.id); },
                "scope": function(_d) { return scopes.has(_d.id); }
            });

    });
}


function clearHighlights(id) {
    d3.select(id).selectAll(".node").classed(
        {"in": false, "out": false, "labelset": false, "scope": false}
    );
    d3.select(id).selectAll(".link").classed(
        {"in": false, "out": false, "labelset": false, "scope": false}
    );
}


function toggleSticky(id, node, d) {
    if (d.sticky) {
        d.sticky = false;
        d3.select(node).classed("selected", false);
    } else {
        d3.select(id).selectAll(".node.selected").each(function(_d) {
            _d.sticky = false;
            d3.select(this).classed("selected", false);
        });
        d.sticky = true;
        d3.select(node).classed("selected", true);
    }
    return d.sticky;
}


function clearVizArtifacts() {
  d3.select("#visualizations").html("");
}
