function visualizeSentence(xml_text) {
	clearVizArtifacts();
	clearAlertMessage();
	
	displayAlert('Visualizing...', 'alert-info');
	
	if (xml_text) {
		d3_graph = parseXmlDMRS(xml_text)
		
		if (d3_graph) {
			showGraphs(d3_graph);
			clearAlertMessage();
		}
	} else {
		displayAlert('<b>Error:</b> No XML provided.', 'alert-danger');
	}
}


function clearAlertMessage() {
	$("#alert_placeholder").html("");
}


function resetVisualizer() {
	clearVizArtifacts();
	clearAlertMessage();
	$("#dmrsinput").val("");
}


function parseXmlDMRS(xml_text) {	
	// Remove line breaks 
	xml_text = xml_text.replace(/(\r\n|\n|\r)/gm,"");
	
	// Parse XML
	try {
		xmlDoc = $.parseXML(xml_text);
	}
	catch(err) {
		displayAlert('<b>Error parsing XML.</b> ', 'alert-danger');
		return null
	}
	
	xml = $(xmlDoc);
	
	// Parse nodes into objects
	nodes = xml.find('node');
	d3_nodes = [];
	
	node_map = {};
	
	for (i = 0; i < nodes.length; i++) {
		node = nodes[i];
		
		node_map[node.getAttribute('nodeid')] = i;
		
		sortinfo = node.getElementsByTagName('sortinfo')[0];
		
		d3_node = {
			id: node.getAttribute('nodeid'),
			pred: parseNodePred(node),
			cfrom: node.getAttribute('cfrom'),
			cto: node.getAttribute('cto'),
			cvarsort: sortinfo.getAttribute('cvarsort'),
			carg: node.getAttribute('carg'),
			varprops: parseNodeProperties(node)
		};
	
		d3_nodes.push(d3_node);
	}
	
	// Parse links into objects
	links = xml.find('link');
	d3_links = [];
	for (i = 0; i < links.length; i++) {
		link = links[i];
		rargname = link.getElementsByTagName('rargname')[0];
		post = link.getElementsByTagName('post')[0];
		
		d3_link = {
			source: node_map[link.getAttribute('from')],
			target: node_map[link.getAttribute('to')],
			start: link.getAttribute('from'),
			end: link.getAttribute('to'),
			rargname: rargname.textContent,
			post: post.textContent
		};
		
		d3_links.push(d3_link);
	}
	
	d3_graph = {
		nodes: d3_nodes,
		links: d3_links
	};
	
	return d3_graph;
}


function parseNodePred(node) {
	realpred = node.getElementsByTagName('realpred');
		
	if (realpred.length > 0) {
		pred_elements = [
			'',
			realpred[0].getAttribute('lemma'),
			realpred[0].getAttribute('pos'),
			realpred[0].getAttribute('sense')
		];
		pred = pred_elements.join('_')
	}
	else {
		gpred = node.getElementsByTagName('gpred')[0].textContent;
		pred = gpred.replace('_rel', '')
	}

	return pred;
}


function parseNodeProperties(node) {
	
	sortinfo = node.getElementsByTagName('sortinfo')[0];
	
	property_names = ['ind', 'pers', 'num', 'gend', 'sf', 'mood', 'tense', 'prog', 'perf'];
	properties = {};
	
	for (j = 0; j < property_names.length; j++) {
		property_name = property_names[j];
		if (sortinfo.getAttribute(property_name) != null) {
			properties[property_name.toUpperCase()] = sortinfo.getAttribute(property_name);
		};
	}
	
	return properties;
}


function displayAlert(errorMessage, type) {
	bootstrap_alert = function() {}
	bootstrap_alert.warning = function(message) {
            $('#alert_placeholder').html('<div class="alert '+type+'"><span>'+message+'</span></div>')
        }
    
	bootstrap_alert.warning(errorMessage);
}



function showGraphs(graph) {

	var svg = d3.select("#visualizations")
		.selectAll('.result')
		.data([graph])
		.enter()
		.append("svg")
		.attr("id", "dmrs")
		.attr("width", "100%")
		.attr("height", "100%")
		.attr("cursor", "grab")
		.call(d3.behavior.zoom().on("zoom", function () {
        svg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")
		}))
		.append("g")
		
	svg.attr("id", function(d, i) { return "dmrs" + i; })
		.each(function(d, i) { dmrsDisplay(this, d); });
}