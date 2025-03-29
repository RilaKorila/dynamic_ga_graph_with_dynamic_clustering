package ocha.itolab.koala.core.data;

import java.io.*;
import java.util.*;

import ocha.itolab.koala.core.mesh.MeshGenerator;

public class TulipFileReader {
	static Graph graph = null;
	static BufferedReader breader = null;
	static String directory;

	public static Graph readConnectivity(String filename, final int timestamp) {
		graph = new Graph();
		open(filename);
		read();
		close();

		graph.mesh = MeshGenerator.generate(graph, timestamp);
		return graph;
	}

	static void open(String filename) {
		try {
			File file = new File(filename);
			breader = new BufferedReader(new FileReader(file));
			breader.ready();
			directory = file.getParent() + "/";
		} catch (Exception e) {
			System.err.println(e);
		}
	}

	static void close() {
		try {
			breader.close();
		} catch (Exception e) {
			System.err.println(e);
		}
	}

	static void read() {
		boolean isProperty = false;

		graph.vectorname = new String[2];
		for (int i = 0; i < graph.vectorname.length; i++)
			graph.vectorname[i] = Integer.toString(i);
		graph.attributeType = graph.ATTRIBUTE_VECTOR;

		try {

			while (true) {
				String line = breader.readLine();
				if (line == null)
					break;

				if (line.indexOf("property") >= 0) {
					isProperty = true;
					continue;
				}

				if (isProperty == false && line.startsWith("(nodes 0..")) {
					line = line.substring(10);
					line = line.replace(")", "");
					int numnode = Integer.parseInt(line) + 1;
					allocateNodes(numnode);
				} else if (isProperty == false && line.startsWith("(nodes 0")) {
					line = line.substring(10);
					line = line.replace(")", "");
					StringTokenizer token = new StringTokenizer(line);
					int numnode = 0;
					while (token.countTokens() > 0) {
						numnode = Integer.parseInt(token.nextToken()) + 1;
					}
					allocateNodes(numnode);
				}

				if (isProperty == false && line.startsWith("(edge")) {
					line = line.replace(")", "");
					StringTokenizer token = new StringTokenizer(line);
					token.nextToken();
					token.nextToken();
					int nid1 = Integer.parseInt(token.nextToken());
					int nid2 = Integer.parseInt(token.nextToken());
					Node node1 = graph.nodes.get(nid1);
					Node node2 = graph.nodes.get(nid2);
					Edge edge = new Edge();
					edge.id = graph.edges.size();
					graph.edges.add(edge);
					edge.nodes[0] = node1;
					edge.nodes[1] = node2;
					node1.connectedEdge.add(edge);
					node2.connectingEdge.add(edge);

				}

			}

		} catch (Exception e) {
			e.printStackTrace();
		}

		postprocess(graph);
	}

	static void allocateNodes(int numnode) {
		for (int i = 0; i < numnode; i++) {
			Node node = new Node();
			node.id = graph.nodes.size();
			node.dissim1 = new double[numnode];
			graph.nodes.add(node);
			node.vector = new double[graph.vectorname.length];
			node.colorId = -1;
			for (int j = 0; j < node.vector.length; j++)
				node.vector[j] = 1.0;
		}
	}

	static void postprocess(Graph graph) {

		for (int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);
			int numc1 = node.connectedEdge.size();
			int numc2 = node.connectingEdge.size();
			node.connected = new int[numc1];
			node.connecting = new int[numc2];
			for (int j = 0; j < node.connectedEdge.size(); j++) {
				Edge e = node.connectedEdge.get(j);
				node.connected[j] = e.id;
			}
			for (int j = 0; j < node.connectingEdge.size(); j++) {
				Edge e = node.connectingEdge.get(j);
				node.connecting[j] = e.id;
			}
		}

	}

}
