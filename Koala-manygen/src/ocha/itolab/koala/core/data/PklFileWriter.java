package ocha.itolab.koala.core.data;

import java.io.*;

public class PklFileWriter {
	static BufferedWriter writer = null;
	static double xmin, xmax, ymin, ymax;
	
	public static void write(Graph graph, String filename) {
		String line = "";
		xmin = ymin = 1.0e+30;   xmax = ymax = -1.0e+30;
		double WIDTH = 1000.0, HEIGHT = 1000.0;
		
		openWriter(filename);
		
		// calculate the ratio
		for(int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);	
			int nid = node.id;
			int mid = node.vertex.getId();
			double x = node.x;
			double y = node.y;
			xmin = (xmin < x) ? xmin : x;
			xmax = (xmax > x) ? xmax : x;
			ymin = (ymin < y) ? ymin : y;
			ymax = (ymax > y) ? ymax : y;
		}
		double rw = WIDTH / (xmax - xmin);
		double rh = HEIGHT / (ymax - ymin);
		
		// write id:
		println("id:");
		println("0");
		
		// write nodes
		println("nodelist:");
		println("[");
		// for each node
		for(int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);	
			int nid = node.id;
			int mid = node.vertex.getId();
			double x = node.x;
			double y = node.y;
			x = (x - xmin) * rw;
			y = (y - ymin) * rh;
			line = "[" + nid + "," + mid + "," + x + "," + y + ",0.01,#888888],";
			println(line);
		}
		println("]");
		
		// write lines
		println("linelist:");
		println("[");
		// for each edge
		for(int i = 0; i < graph.edges.size(); i++) {
			Edge edge = graph.edges.get(i);	
			Node n1 = edge.nodes[0];
			Node n2 = edge.nodes[1];
			println("[" + n1.id + "," + n2.id + "],");
		}
		println("]");
		
		// width and height
		println("width:");
		println(Double.toString(WIDTH));
		println("height:");
		//println("1000");
		println(Double.toString(HEIGHT));
		
		closeWriter();
	}
	
	
	
	static BufferedWriter openWriter(String filename) {	
		try {
			 writer = new BufferedWriter(
					 new OutputStreamWriter(new FileOutputStream(new File(filename)),"SJIS"));
		} catch (Exception e) {
			System.err.println(e);
			return null;
		}
		return writer;
	}
	

	static void closeWriter() {
		
		try {
			writer.close();
		} catch (Exception e) {
			System.err.println(e);
			return;
		}
	}
	

	static void println(String word) {
		try {
			writer.write(word, 0, word.length());
			writer.flush();
			writer.newLine();
		} catch (Exception e) {
			System.err.println(e);
			return;
		}
	}	
	
}
