package ocha.itolab.koala.evaluate.sprawlter;

import java.io.*;
import java.util.*;

import ocha.itolab.koala.constants.ResourceFile;
import ocha.itolab.koala.core.data.*;
import ocha.itolab.koala.core.mesh.*;

public class SprawlterEvaluator {
	static double NN_ALPHA = 0.25, NE_ALPHA = 0.25, EE_ALPHA = 0.1;

	static String path = ResourceFile.EVALUATE_RESULT.path();
	static String filenames[];
	static double sprawls[], nnpens[], nepens[], eepens[], result[], result2[], result3[];
	static double maxnn = 0.0, maxne = 0.0, maxee = 0.0;
	static int counter = 0;

	static ArrayList<MetaEdge> metaedges = new ArrayList<MetaEdge>();

	static class MetaEdge {
		Vertex v1, v2;
		int counter;
	}

	/**
	 * main method
	 */
	public static void main(String args[]) {

		// retrieve file names
		File dir = new File(path);
		filenames = dir.list();
		result = new double[filenames.length];
		result2 = new double[filenames.length];
		result3 = new double[filenames.length];
		sprawls = new double[filenames.length];
		nnpens = new double[filenames.length];
		nepens = new double[filenames.length];
		eepens = new double[filenames.length];

		// calculate penalty (first)
		for (counter = 0; counter < filenames.length; counter++) {
			// for(counter = 0; counter < 1000; counter++) {
			Graph graph = LayoutFileReader.read(path + filenames[counter]);
			preprocess(graph);
			calcPenaltyOneGraph(graph, 1);
			if (counter % 100 == 0)
				System.out.println(" #calcPenaltyOneGraph (phase 1) " + counter + "/" + filenames.length);
		}

		// calculate penalty (second phase)
		for (counter = 0; counter < filenames.length; counter++) {
			// for(counter = 0; counter < 1000; counter++) {
			Graph graph = LayoutFileReader.read(path + filenames[counter]);
			preprocess(graph);
			calcPenaltyOneGraph(graph, 2);
			if (counter % 100 == 0)
				System.out.println(" #calcPenaltyOneGraph (phase 2) " + counter + "/" + filenames.length);
		}

		// normalize penalty
		normalizePenalty();

	}

	/**
	 * Evaluate one graph
	 */
	public static void calcPenaltyOneGraph(Graph graph, int phase) {
		double sprawl = calcSprawl(graph);
		double nnpen = calcNodeNodePenalty(graph, phase);
		double nepen = calcNodeEdgePenalty(graph, phase);
		double eepen = calcEdgeEdgePenalty(graph);
		sprawls[counter] = sprawl;
		nnpens[counter] = nnpen;
		nepens[counter] = nepen;
		eepens[counter] = eepen;

		// System.out.println("phase" + phase + ": graph" + counter + " s=" + sprawl + "
		// nn=" + nnpen + " ne=" + nepen + " ee=" + eepen);
	}

	/**
	 * Preprocess
	 */
	public static void preprocess(Graph graph) {
		metaedges.clear();

		// for each edge
		for (int i = 0; i < graph.edges.size(); i++) {
			Edge e = graph.edges.get(i);
			// 両端のmetanodeを取得
			Vertex v1 = e.getNode()[0].getVertex();
			Vertex v2 = e.getNode()[1].getVertex();

			// for each metaedge
			boolean isFound = false;
			for (int j = 0; j < metaedges.size(); j++) {
				// 既存のmetaedgeに含まれるか調査
				MetaEdge me = metaedges.get(j);
				if (me.v1 == v1 && me.v2 == v2) {
					me.counter++;
					isFound = true;
					break;
				}
				if (me.v1 == v2 && me.v2 == v1) {
					me.counter++;
					isFound = true;
					break;
				}
			}
			// 新しいmetaedgeであれば追加
			if (isFound == false) {
				MetaEdge me = new MetaEdge();
				me.v1 = v1;
				me.v2 = v2;
				me.counter = 1;
				metaedges.add(me);
			}
		}

	}

	/**
	 * Calculate sprawl
	 */
	public static double calcSprawl(Graph graph) {
		double sprawl = 0.0;
		double minx = 1.0e+30, miny = 1.0e+30, maxx = -1.0e+30, maxy = -1.0e+30;
		double zoom = 500.0;
		// double zoom = 1.0;
		// Pyvisでのsize=2が、どのsizeかは不明
		double node_area = 2.0 * 2.0 * Math.PI;

		// for each vertex
		for (int i = 0; i < graph.mesh.getNumVertices(); i++) {
			Vertex v = graph.mesh.getVertex(i);
			double pos[] = v.getPosition();
			double r = v.getRadius();
			double x1 = (pos[0] - r) * zoom;
			double x2 = (pos[0] + r) * zoom;
			double y1 = (pos[1] - r) * zoom;
			double y2 = (pos[1] + r) * zoom;
			minx = (minx < x1) ? minx : x1;
			miny = (miny < y1) ? miny : y1;
			maxx = (maxx > x1) ? maxx : x1;
			maxy = (maxy > y1) ? maxy : y1;
			minx = (minx < x2) ? minx : x2;
			miny = (miny < y2) ? miny : y2;
			maxx = (maxx > x2) ? maxx : x2;
			maxy = (maxy > y2) ? maxy : y2;
		}

		// sprawl = (maxx - minx) * (maxy - miny) / (double)graph.nodes.size();
		sprawl = (maxx - minx) * (maxy - miny) / ((double) graph.nodes.size() * node_area);
		// System.out.println("maxx: " + maxx + ", minx: " + minx);
		// System.out.println("maxy: " + maxy + ", miny: " + miny);
		// System.out.println("graph nodes: " + (double)graph.nodes.size());
		return sprawl;
	}

	/**
	 * Calculate sprawl of forcused vertex
	 */
	public static double calcSprawlOfForcusedVertex(Graph graph) {
		double sprawl = 0.0;
		double minx = 1.0e+30, miny = 1.0e+30, maxx = -1.0e+30, maxy = -1.0e+30;
		double zoom = 500.0;
		// double zoom = 1.0;
		double node_area = 0.0;

		// for each vertex
		for (int i = 0; i < graph.mesh.getNumVertices(); i++) {
			Vertex v = graph.mesh.getVertex(i);

			// isForcused が false なら計算しない
			if (!v.getIsForcused())
				continue;

			double pos[] = v.getPosition();
			double r = v.getRadius();
			double x1 = (pos[0] - r) * zoom;
			double x2 = (pos[0] + r) * zoom;
			double y1 = (pos[1] - r) * zoom;
			double y2 = (pos[1] + r) * zoom;
			node_area += Math.PI * (r * zoom) * (r * zoom);
			minx = (minx < x1) ? minx : x1;
			miny = (miny < y1) ? miny : y1;
			maxx = (maxx > x2) ? maxx : x2;
			maxy = (maxy > y2) ? maxy : y2;
		}

		// sprawl = (maxx - minx) * (maxy - miny) / (double)graph.nodes.size();
		sprawl = (maxx - minx) * (maxy - miny) / node_area;
		// System.out.println("maxx: " + maxx + ", minx: " + minx);
		// System.out.println("maxy: " + maxy + ", miny: " + miny);
		// System.out.println("graph nodes: " + (double)graph.nodes.size());
		return sprawl;
	}

	/**
	 * Calculate node-node overlap penalty
	 */
	public static double calcNodeNodePenalty(Graph graph, int phase) {
		double penalty = 0.0;
		double p0 = 0.0;
		if (phase == 1)
			maxnn = 0.0;

		// for each vertex pair
		for (int i = 0; i < graph.mesh.getNumVertices(); i++) {
			Vertex v1 = graph.mesh.getVertex(i);
			double p1[] = v1.getPosition();
			double r1 = v1.getRadius();
			for (int j = (i + 1); j < graph.mesh.getNumVertices(); j++) {
				Vertex v2 = graph.mesh.getVertex(j);
				double p2[] = v2.getPosition();
				double r2 = v2.getRadius();

				// calculate distance between circles
				double diffr = (r1 > r2) ? (r1 - r2) : (r2 - r1);
				double dist = Math.sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]));
				// System.out.println(" r1=" + r1 + " r2=" + r2 + " dist=" + dist);
				if ((r1 + r2) < dist)
					continue;

				// if a circle encloses another circle
				if (dist < diffr) {
					if (r1 > r2) {
						p0 = Math.sqrt(r2 * r2 * Math.PI);
						continue;
					} else {
						p0 = Math.sqrt(r1 * r1 * Math.PI);
						continue;
					}
				}

				// if circles partially overlap
				else {
					double cos1 = (dist * dist + r1 * r1 - r2 * r2) / (2 * dist * r1);
					double cos2 = (dist * dist + r2 * r2 - r1 * r1) / (2 * dist * r2);
					p0 = r1 * r1 * Math.acos(cos1) + r2 * r2 * Math.acos(cos2)
							- 0.5 * Math.sqrt(4 * dist * dist * r1 * r1
									- (dist * dist + r1 * r1 - r2 * r2) * (dist * dist + r1 * r1 - r2 * r2));
				}

				// Add the penalty
				if (phase == 1) {
					maxnn = (maxnn > p0) ? maxnn : p0;
				} else {
					p0 = (1 - NN_ALPHA) * Math.pow((2.0 * p0), 0.7) + NN_ALPHA * Math.pow(maxnn, 0.7);
				}
				penalty += p0;

			}
		}

		return penalty;
	}

	/**
	 * Calculate node-node overlap penalty of forcused vertex
	 */
	public static double calcNodeNodePenaltyOfForcusedVertex(Graph graph, int phase) {
		double penalty = 0.0;
		double p0 = 0.0;
		if (phase == 1)
			maxnn = 0.0;

		// for each vertex pair
		for (int i = 0; i < graph.mesh.getNumVertices(); i++) {
			Vertex v1 = graph.mesh.getVertex(i);

			// isForcused が false なら計算しない
			if (!v1.getIsForcused())
				continue;

			double p1[] = v1.getPosition();
			double r1 = v1.getRadius();
			for (int j = (i + 1); j < graph.mesh.getNumVertices(); j++) {
				Vertex v2 = graph.mesh.getVertex(j);

				// 片方が isForcused = true なら計算する条件にするためコメントアウト
				// isForcused が false なら計算しない
				// if (!v2.getIsForcused()) continue;

				double p2[] = v2.getPosition();
				double r2 = v2.getRadius();

				// calculate distance between circles
				double diffr = (r1 > r2) ? (r1 - r2) : (r2 - r1);
				double dist = Math.sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]));
				// System.out.println(" r1=" + r1 + " r2=" + r2 + " dist=" + dist);
				if ((r1 + r2) < dist)
					continue;

				// if a circle encloses another circle
				if (dist < diffr) {
					if (r1 > r2) {
						p0 = Math.sqrt(r2 * r2 * Math.PI);
						continue;
					} else {
						p0 = Math.sqrt(r1 * r1 * Math.PI);
						continue;
					}
				}

				// if circles partially overlap
				else {
					double cos1 = (dist * dist + r1 * r1 - r2 * r2) / (2 * dist * r1);
					double cos2 = (dist * dist + r2 * r2 - r1 * r1) / (2 * dist * r2);
					p0 = r1 * r1 * Math.acos(cos1) + r2 * r2 * Math.acos(cos2)
							- 0.5 * Math.sqrt(4 * dist * dist * r1 * r1
									- (dist * dist + r1 * r1 - r2 * r2) * (dist * dist + r1 * r1 - r2 * r2));
				}

				// Add the penalty
				if (phase == 1) {
					maxnn = (maxnn > p0) ? maxnn : p0;
				} else {
					p0 = (1 - NN_ALPHA) * Math.pow((2.0 * p0), 0.7) + NN_ALPHA * Math.pow(maxnn, 0.7);
				}
				penalty += p0;

			}
		}

		return penalty;
	}

	/**
	 * Calculate node-edge overlap penalty
	 */
	public static double calcNodeEdgePenalty(Graph graph, int phase) {
		double penalty = 0.0;
		if (phase == 1)
			maxne = 0.0;

		// for each metaedge
		for (int i = 0; i < metaedges.size(); i++) {
			// metaedgeの両端のmetanodeの中心座標をそのmetaedgeの両端の座標(ex1, ey1), (ex2, ey2)として計算
			MetaEdge me = metaedges.get(i);
			double ex1 = me.v1.getPosition()[0];
			double ey1 = me.v1.getPosition()[1];
			double ex2 = me.v2.getPosition()[0];
			double ey2 = me.v2.getPosition()[1];
			double ea = ex2 - ex1;
			double eb = ey2 - ey1;
			double ec = -(ea * ex1 + eb * ey1);

			// for each vertex
			for (int j = 0; j < graph.mesh.getNumVertices(); j++) {
				Vertex vertex = graph.mesh.getVertex(j);
				double c[] = vertex.getPosition();
				double r = vertex.getRadius();
				double D = Math.abs(ea * c[0] + eb * c[1] + ec);
				double eab = ea * ea + eb * eb;
				double det = eab * r * r - D * D;
				if (det <= 0.0)
					continue;
				det = Math.sqrt(det);
				double cx1 = c[0] + (ea * D - eb * det) / eab;
				double cy1 = c[1] + (eb * D + ea * det) / eab;
				double cx2 = c[0] + (ea * D + eb * det) / eab;
				double cy2 = c[1] + (eb * D - ea * det) / eab;
				if (cx1 > ex1 && cx1 > ex2 && cx2 > ex1 && cx2 > ex2)
					continue;
				if (cx1 < ex1 && cx1 < ex2 && cx2 < ex1 && cx2 < ex2)
					continue;
				double len = Math.sqrt((cx2 - cx1) * (cx2 - cx1) + (cy2 - cy1) * (cy2 - cy1));

				if (phase == 1) {
					maxne = (maxne > len) ? maxne : len;
				} else {
					len = 2.0 * (1.0 - NE_ALPHA) * len + NE_ALPHA * maxne;
				}
				penalty += (len * me.counter);
			}

		}

		return penalty;
	}

	/**
	 * Calculate node-edge overlap penalty of forcused vertex
	 */
	public static double calcNodeEdgePenaltyOfForcusedVertex(Graph graph, int phase) {
		double penalty = 0.0;

		if (phase == 1)
			maxne = 0.0;

		// for each metaedge
		for (int i = 0; i < metaedges.size(); i++) {
			// metaedgeの両端のmetanodeの中心座標をそのmetaedgeの両端の座標(ex1, ey1), (ex2, ey2)として計算
			MetaEdge me = metaedges.get(i);
			double ex1 = me.v1.getPosition()[0];
			double ey1 = me.v1.getPosition()[1];
			double ex2 = me.v2.getPosition()[0];
			double ey2 = me.v2.getPosition()[1];
			double ea = ex2 - ex1;
			double eb = ey2 - ey1;
			double ec = -(ea * ex1 + eb * ey1);

			// for each vertex
			for (int j = 0; j < graph.mesh.getNumVertices(); j++) {
				Vertex vertex = graph.mesh.getVertex(j);

				// isForcused が false なら計算しない
				if (!vertex.getIsForcused())
					continue;

				double c[] = vertex.getPosition();
				double r = vertex.getRadius();
				double D = Math.abs(ea * c[0] + eb * c[1] + ec);
				double eab = ea * ea + eb * eb;
				double det = eab * r * r - D * D;
				if (det <= 0.0)
					continue;
				det = Math.sqrt(det);
				double cx1 = c[0] + (ea * D - eb * det) / eab;
				double cy1 = c[1] + (eb * D + ea * det) / eab;
				double cx2 = c[0] + (ea * D + eb * det) / eab;
				double cy2 = c[1] + (eb * D - ea * det) / eab;
				if (cx1 > ex1 && cx1 > ex2 && cx2 > ex1 && cx2 > ex2)
					continue;
				if (cx1 < ex1 && cx1 < ex2 && cx2 < ex1 && cx2 < ex2)
					continue;
				double len = Math.sqrt((cx2 - cx1) * (cx2 - cx1) + (cy2 - cy1) * (cy2 - cy1));

				if (phase == 1) {
					maxne = (maxne > len) ? maxne : len;
				} else {
					len = 2.0 * (1.0 - NE_ALPHA) * len + NE_ALPHA * maxne;
				}
				penalty += (len * me.counter);
			}
		}
		return penalty;
	}

	/**
	 * Calculate edge-edge overlap penalty
	 */
	public static double calcEdgeEdgePenalty(Graph graph) {
		double PENALTY_CONST = 1.0;
		double penalty = 0.0;

		// for each edge pair
		for (int i = 0; i < metaedges.size(); i++) {
			MetaEdge me = metaedges.get(i);
			double x11 = me.v1.getPosition()[0];
			double y11 = me.v1.getPosition()[1];
			double x12 = me.v2.getPosition()[0];
			double y12 = me.v2.getPosition()[1];
			double x1v = x12 - x11;
			double y1v = y12 - y11;
			double len1 = Math.sqrt(x1v * x1v + y1v * y1v);
			if (len1 < 1.0e-8)
				continue;

			for (int j = (i + 1); j < metaedges.size(); j++) {
				MetaEdge me2 = metaedges.get(j);
				double x21 = me2.v1.getPosition()[0];
				double y21 = me2.v1.getPosition()[1];
				double x22 = me2.v2.getPosition()[0];
				double y22 = me2.v2.getPosition()[1];

				// metaedge同士の交差を判断
				final var isMetaEdgesCrossing = checkMetaEdgeCrossing(
						x11, x12, y11, y12, x21, x22, y21, y22);
				if (!isMetaEdgesCrossing)
					continue;

				double x2v = x22 - x21;
				double y2v = y22 - y21;
				double len2 = Math.sqrt(x2v * x2v + y2v * y2v);
				if (len2 < 1.0e-8)
					continue;

				// calculate the inner product as the penalty
				// inner: 内積の公式によって求めた cosθ
				double inner = Math.abs(x1v * x2v + y1v * y2v) / (len1 * len2) + PENALTY_CONST;
				penalty += (inner * me.counter * me2.counter);
			}
		}
		return penalty;
	}

	/**
	 * (x11, y11), (x12, y12), (x21, y21), (x22, y22)で構成される2直線が
	 * 交差しているかを判定する
	 * 判定ロジック：https://qiita.com/zu_rin/items/e04fdec4e3dec6072104
	 */
	private static boolean checkMetaEdgeCrossing(double x11, double x12, double y11, double y12, double x21, double x22,
			double y21, double y22) {
		double s = (x11 - x12) * (y21 - y11) - (y11 - y12) * (x21 - x11);
		double t = (x11 - x12) * (y22 - y11) - (y11 - y12) * (x22 - x11);
		if (s * t > 0)
			return false;
		s = (x21 - x22) * (y11 - y21) - (y21 - y22) * (x11 - x21);
		t = (x21 - x22) * (y12 - y21) - (y21 - y22) * (x12 - x21);
		if (s * t > 0)
			return false;

		return true;
	}

	/**
	 * Normalize penalty
	 */
	public static void normalizePenalty() {
		double NN_RATIO = 1.0, NE_RATIO = 1.0, EE_RATIO = 1.0, EE_RATIO2 = 0.5, EE_RATIO3 = 0.0;
		double nnmin = 1.0e+30, nnmax = -1.0e+30;
		double nemin = 1.0e+30, nemax = -1.0e+30;
		double eemin = 1.0e+30, eemax = -1.0e+30;
		double MIN = 1.0, MAX = 10.0, EPSILON = 0.001;

		// for each graph
		for (int i = 0; i < result.length; i++) {
			nnmin = (nnmin < nnpens[i]) ? nnmin : nnpens[i];
			nemin = (nemin < nepens[i]) ? nemin : nepens[i];
			eemin = (eemin < eepens[i]) ? eemin : eepens[i];
			nnmax = (nnmax > nnpens[i]) ? nnmax : nnpens[i];
			nemax = (nemax > nepens[i]) ? nemax : nepens[i];
			eemax = (eemax > eepens[i]) ? eemax : eepens[i];
		}

		System.out.println("nn[" + nnmin + "," + nnmax + "] ne[" + nemin + "," + nemax + "] ee[" + eemin + "," + eemax);

		// for each graph
		for (int i = 0; i < result.length; i++) {
			double vnn = (nnpens[i] - nnmin) / (nnmax - nnmin);
			double vne = (nepens[i] - nemin) / (nemax - nemin);
			double vee = (eepens[i] - eemin) / (eemax - eemin);
			vnn = vnn * (MAX - MIN) + MIN;
			vne = vne * (MAX - MIN) + MIN;
			vee = vee * (MAX - MIN) + MIN;
			nnpens[i] = Math.sqrt(sprawls[i] * vnn);
			nepens[i] = Math.sqrt(sprawls[i] * vne);
			eepens[i] = Math.sqrt(sprawls[i] * vee);
			result[i] = NN_RATIO * nnpens[i] + NE_RATIO * nepens[i] + EE_RATIO * eepens[i];
			result2[i] = NN_RATIO * nnpens[i] + NE_RATIO * nepens[i] + EE_RATIO2 * eepens[i];
			result3[i] = NN_RATIO * nnpens[i] + NE_RATIO * nepens[i] + EE_RATIO3 * eepens[i];
			// System.out.println(filenames[i] + " RESULT=" + result[i] + " nn=" + nnpens[i]
			// + " ne=" + nepens[i] + " ee=" + eepens[i]);
			System.out.println(filenames[i] + "," + result[i] + "," + result2[i] + "," + result3[i] + "," + nnpens[i]
					+ "," + nepens[i] + "," + eepens[i]);
		}
	}

}
