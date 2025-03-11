package ocha.itolab.koala.core.data;

import java.io.*;
import java.util.StringTokenizer;

public class GraphFileReader {
	static Graph graph = null;
	static BufferedReader breader = null;
	static String directory;

	public static Graph readConnectivity(String filename) {
		graph = new Graph();
		// System.out.println(filename);

		open(filename);
		read();
		close();

		graph.postprocess();
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
		int phase = 0;
		Node node = null;

		try {

			while (true) {
				String line = breader.readLine();
				if (line == null)
					break;
				if (line.startsWith("#connectivity"))
					continue;

				if (line.startsWith("#vector") == true) {
					StringTokenizer token = new StringTokenizer(line, ",");
					token.nextToken();
					graph.vectorname = new String[token.countTokens()];
					for (int i = 0; i < graph.vectorname.length; i++)
						graph.vectorname[i] = token.nextToken();
					readVector();
					return;
				}
				if (line.startsWith("#dissimilarity") == true) {
					readDissimilarity();
					return;
				}

				StringTokenizer token = new StringTokenizer(line, ",");

				if (phase == 0) {
					node = new Node();
					node.id = graph.nodes.size();
					graph.nodes.add(node);
					token.nextToken();
					int ndesc = token.countTokens();
					node.description = new String[ndesc];
					for (int i = 0; i < ndesc; i++)
						node.description[i] = token.nextToken();

				} else if (phase == 1) {
					int n = token.countTokens();
					node.connected = new int[n];
					for (int i = 0; i < n; i++) {
						node.connected[i] = Integer.parseInt(token.nextToken());
					}
				} else if (phase == 2) {
					int n = token.countTokens();
					node.connecting = new int[n];
					for (int i = 0; i < n; i++) {
						node.connecting[i] = Integer.parseInt(token.nextToken());
					}
				}

				phase = (phase == 2) ? 0 : (phase + 1);
			}

		} catch (Exception e) {
			e.printStackTrace();
		}

	}

	static void readVector() {
		int count = 0;
		graph.attributeType = graph.ATTRIBUTE_VECTOR;

		try {
			while (true) {
				String line = breader.readLine();
				if (line == null)
					break;
				StringTokenizer token = new StringTokenizer(line, ",");
				token.nextToken();

				Node node = graph.nodes.get(count++);
				node.vector = new double[graph.vectorname.length];
				node.colorId = -1;
				double maxvalue = -1.0e+30, minvalue = 0.01;
				for (int i = 0; i < graph.vectorname.length; i++) {
					String v = token.nextToken();
					double value = Double.parseDouble(v);
					node.vector[i] = value;
					if (maxvalue < value && minvalue < value) {
						maxvalue = value;
						node.colorId = i;
					}
				}

			}

		} catch (Exception e) {
			e.printStackTrace();
		}

	}

	static void readDissimilarity() {
		int count = 0;
		graph.attributeType = graph.ATTRIBUTE_DISSIM;

		try {
			while (true) {

				String line = breader.readLine();
				if (line == null)
					break;
				StringTokenizer token = new StringTokenizer(line, ",");
				token.nextToken();

				Node node = graph.nodes.get(count++);
				node.dissim1 = new double[graph.nodes.size()];
				node.colorId = Integer.parseInt(token.nextToken());

				for (int i = 0; i < graph.nodes.size(); i++) {
					String v = token.nextToken();
					double value = Double.parseDouble(v);
					node.dissim1[i] = value;
				}
			}

		} catch (Exception e) {
			e.printStackTrace();
		}
	}

}
