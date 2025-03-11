package ocha.itolab.koala.core.data;

import java.io.*;

// import com.jogamp.opengl.GL2;

import ocha.itolab.koala.core.mesh.*;

public class LayoutFileWriter {
	static BufferedWriter bwriter;

	public static void write(Graph graph, String filename) {
		String line;
		System.out.println("LayoutFileWriter#write: " + filename);

		openWriter(filename);

		// nodes
		writeOneLine("#nodes" + "," + graph.nodes.size());
		for (int i = 0; i < graph.nodes.size(); i++) {
			Node node = graph.nodes.get(i);

			// node description
			// id, x座標, y座標, 所属する親ノードのid, nodeと対応する著者名
			line = Integer.toString(i) + "," + node.x + "," + node.y + "," + node.vertex.getId();
			for (int j = 0; j < node.getNumDescription(); j++)
				line += ("," + node.getDescription(j));
			writeOneLine(line);
		}

		// edges
		writeOneLine("#edges" + "," + graph.edges.size());
		for (int i = 0; i < graph.edges.size(); i++) {
			Edge edge = graph.edges.get(i);
			Node node1 = edge.nodes[0];
			Node node2 = edge.nodes[1];

			// edge description
			line = Integer.toString(i) + "," + node1.id + "," + node2.id;
			writeOneLine(line);
			// writeBundledEdgePositions(i, node1, node2);
		}

		// clusters
		Mesh mesh = graph.mesh;
		writeOneLine("#clusters" + "," + mesh.getNumVertices());
		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex vertex = mesh.getVertex(i);

			// cluster description
			line = Integer.toString(i) + "," + vertex.getPosition()[0] + "," + vertex.getPosition()[1] + ","
					+ vertex.getRadius();
			writeOneLine(line);
			line = "";
			for (int j = 0; j < vertex.getNodes().size(); j++)
				line += ("," + vertex.getNodes().get(j).id);
			writeOneLine(line);
		}

		closeWriter();
	}

	static void writeBundledEdgePositions(int id, Node n1, Node n2) {
		int NUM_T = 10;
		double ONE_THIRD = 0.33333333333;
		double bundleShape = 0.75;

		double p0[] = new double[2];
		double p1[] = new double[2];
		double p2[] = new double[2];
		double p3[] = new double[2];
		double v1pos[] = n1.vertex.getPosition();
		double v2pos[] = n2.vertex.getPosition();

		p0[0] = n1.getX();
		p0[1] = n1.getY();
		p3[0] = n2.getX();
		p3[1] = n2.getY();

		if (bundleShape > 0.75) {
			p1[0] = v1pos[0];
			p1[1] = v1pos[1];
			p2[0] = v2pos[0];
			p2[1] = v2pos[1];
		} else if (bundleShape > 0.5) {
			double ratio = (bundleShape + 0.5) * 2.0 * ONE_THIRD;
			p1[0] = v1pos[0] * ratio + v2pos[0] * (1.0 - ratio);
			p1[1] = v1pos[1] * ratio + v2pos[1] * (1.0 - ratio);
			p2[0] = v2pos[0] * ratio + v1pos[0] * (1.0 - ratio);
			p2[1] = v2pos[1] * ratio + v1pos[1] * (1.0 - ratio);
		} else {
			double ratio = bundleShape * 2.0;
			p1[0] = (v1pos[0] * 2.0 + v2pos[0]) * ONE_THIRD * ratio
					+ (p0[0] * 2.0 + p3[0]) * ONE_THIRD * (1.0 - ratio);
			p1[1] = (v1pos[1] * 2.0 + v2pos[1]) * ONE_THIRD * ratio
					+ (p0[1] * 2.0 + p3[1]) * ONE_THIRD * (1.0 - ratio);
			p2[0] = (v2pos[0] * 2.0 + v1pos[0]) * ONE_THIRD * ratio
					+ (p3[0] * 2.0 + p0[0]) * ONE_THIRD * (1.0 - ratio);
			p2[1] = (v2pos[1] * 2.0 + v1pos[1]) * ONE_THIRD * ratio
					+ (p3[1] * 2.0 + p0[1]) * ONE_THIRD * (1.0 - ratio);
		}

		String line = Integer.toString(id);
		for (int i = 0; i <= NUM_T; i++) {
			double interval = 1.0 / (double) NUM_T;
			double t0 = interval * (double) i;

			double t1 = 1.0 - t0;
			double bezier0 = t1 * t1 * t1;
			double bezier1 = 3.0 * t0 * t1 * t1;
			double bezier2 = 3.0 * t0 * t0 * t1;
			double bezier3 = t0 * t0 * t0;

			if (bundleShape > 0.75) {
				double pow = (bundleShape - 0.75) * 30.0 + 1.0;
				bezier0 = Math.pow(bezier0, pow);
				bezier3 = Math.pow(bezier3, pow);
				double len = bezier0 + bezier1 + bezier2 + bezier3;
				bezier0 /= len;
				bezier1 /= len;
				bezier2 /= len;
				bezier3 /= len;
			}

			double x = p0[0] * bezier0 + p1[0] * bezier1 + p2[0] * bezier2 + p3[0] * bezier3;
			double y = p0[1] * bezier0 + p1[1] * bezier1 + p2[1] * bezier2 + p3[1] * bezier3;
			// double z = (z1 * (NUM_T - i) + z2 * i) / (double)NUM_T - 0.1;
			// gl2.glVertex3d(pt[0], pt[1], z);
			line += ("," + Double.toString(x) + "," + Double.toString(y));

		}
		writeOneLine(line);

	}

	static BufferedWriter openWriter(String filename) {
		try {
			bwriter = new BufferedWriter(
					new FileWriter(new File(filename)));
			// System.out.println("KoalaFileWriter: " + filename);
		} catch (Exception e) {
			System.err.println(e);
			return null;
		}
		return bwriter;
	}

	static void closeWriter() {

		try {
			bwriter.close();
		} catch (Exception e) {
			System.err.println(e);
			return;
		}
	}

	static void writeOneLine(String word) {
		try {
			bwriter.write(word, 0, word.length());
			bwriter.flush();
			bwriter.newLine();
		} catch (Exception e) {
			System.err.println(e);
			return;
		}
	}
}
