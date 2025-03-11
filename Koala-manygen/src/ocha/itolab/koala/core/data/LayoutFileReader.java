package ocha.itolab.koala.core.data;

import java.io.*;
import java.util.*;
import ocha.itolab.koala.core.mesh.*;

public class LayoutFileReader {
	static BufferedReader breader;
	static Graph graph = null;
	
	public static Graph read(String filename) {

		open(filename);
		if(breader == null) return null;
		graph = new Graph();
		graph.mesh = new Mesh();
		
		int phase = -1;
		Vertex vertex = null;
		try {
			while(true) {
				String line = breader.readLine();
				if(line == null) break;
				StringTokenizer token = new StringTokenizer(line, ",");
				String tag = token.nextToken();
				
				if(tag.startsWith("#nodes") == true) {
					int numnodes = Integer.parseInt(token.nextToken());
					phase = 0;
				}
				else if(tag.startsWith("#edges") == true) {
					int numedges =  Integer.parseInt(token.nextToken());
					phase = 1;
				}
				else if(tag.startsWith("#clusters") == true) {
					int numvertices = Integer.parseInt(token.nextToken());
					phase = 2;
				}
				else if(phase == 0) {
					Node node = new Node();
					node.id = graph.nodes.size();
					graph.nodes.add(node);
					double x = Double.parseDouble(token.nextToken());
					double y = Double.parseDouble(token.nextToken());
					node.setPosition(x, y);
				}
				else if(phase == 1) {
					Edge edge = new Edge();
					edge.id = graph.edges.size();
					graph.edges.add(edge);
					int nid1 = Integer.parseInt(token.nextToken());
					int nid2 = Integer.parseInt(token.nextToken());
					Node n1 = graph.nodes.get(nid1);
					Node n2 = graph.nodes.get(nid2);
					edge.setNode(n1, n2);
				}
				else if(phase == 2) {
					vertex = graph.mesh.addOneVertex();
					double x = Double.parseDouble(token.nextToken());
					double y = Double.parseDouble(token.nextToken());
					vertex.setPosition(x, y, 0.0);
					double r = Double.parseDouble(token.nextToken());
					vertex.setRadius(r);
					phase = 3;
				}
				else if(phase == 3) {
					int nid = Integer.parseInt(tag);
					Node n = graph.nodes.get(nid);
					vertex.addOneNode(n);
					while(token.countTokens() > 0) {
						nid = Integer.parseInt(token.nextToken());
						n = graph.nodes.get(nid);
						vertex.addOneNode(n);
					}
					phase = 2;
				}
				
			}
		} catch(Exception e) {
			e.printStackTrace();
		}
		
		
		close();
		return graph;
	}
	
	
		static void open(String filename) {
		try {
			File file = new File(filename);
			breader = new BufferedReader(new FileReader(file));
			breader.ready();
		} catch (Exception e) {
			breader = null;
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
	
}
