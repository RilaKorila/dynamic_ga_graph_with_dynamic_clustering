package ocha.itolab.koala.core.data;

import java.io.*;

public class KoalaFileWriter {
	static BufferedWriter writer = null;

	public static void write(Graph graph, String filename) {
		String line = "";
		openWriter(filename);
		
		// write connectivity
		println("#connectivity");
		for(int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);	
			line = Integer.toString(i);
			for(int j = 0; j < node.getNumDescription(); j++) {
				line += "," + node.getDescription(j);
			}
			println(line);
			line = "";
			for(int j = 0; j < node.getNumConnectedEdge(); j++) {
				Edge e = node.getConnectedEdge(j);
				Node nn[] = e.getNode();
				if(nn[0] == node) line += "," + nn[1].getId();
				else if(nn[1] == node) line += "," + nn[0].getId();
			}
			println(line);
			line = "";
			for(int j = 0; j < node.getNumConnectingEdge(); j++) {
				Edge e = node.getConnectingEdge(j);
				Node nn[] = e.getNode();
				if(nn[0] == node) line += "," + nn[1].getId();
				else if(nn[1] == node) line += "," + nn[0].getId();
			}
			println(line);
		}
		
		
		// write attribute
		line = "#vector";
		for(int i = 0; i < graph.vectorname.length; i++)
			line += ("," + graph.vectorname[i]);
		println(line);
		for(int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);
			line = Integer.toString(i);
			for(int j = 0; j < node.vector.length; j++)
				line += ("," + node.vector[j]);
			println(line);
		}
		
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
