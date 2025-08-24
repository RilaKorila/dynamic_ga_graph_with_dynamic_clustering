package ocha.itolab.koala.core.mesh;

import ocha.itolab.koala.constants.Dataset;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

import ocha.itolab.koala.core.data.*;

public class MeshGenerator {
	static final int CLUSTERING_BYMYSELF = 1;
	static final int CLUSTERING_LINLOG = 2;
	static final int CLUSTERING_IMPORT = 3;
	static int clusteringMode = CLUSTERING_IMPORT;
	static Dataset dataset = Dataset.NBAF_COAUTHORS; // データ変更

	private static String getClusteringModeName(int mode) { // デバッグ用のメソッド
		switch (mode) {
			case CLUSTERING_BYMYSELF:
				return "CLUSTERING_BYMYSELF";
			case CLUSTERING_LINLOG:
				return "CLUSTERING_LINLOG";
			case CLUSTERING_IMPORT:
				return "CLUSTERING_IMPORT";
			default:
				return "UNKNOWN";
		}
	}

	static double clusteringThreshold = 1.3;
	static int clusteringMaxIteration = 100;
	static int numvThreshold = 1;
	public static double clustersizeRatio = 0.65; // Experiment 1-S

	public static Mesh generate(Graph g, final int timestamp) {
		Mesh m = new Mesh();

		long t1 = System.currentTimeMillis();

		if (clusteringMode == CLUSTERING_BYMYSELF) {

			// 既存のKoala のクラスタリング処理
			// Generate & cluster vertices
			generateVertices(m, g);
			clusterVertices(m, g); // clustering を実施
		}
		if (clusteringMode == CLUSTERING_LINLOG) {
			MeshGeneratorLinLog.execute(m, g);
		}
		if (clusteringMode == CLUSTERING_IMPORT) {
			// ファイルからクラスタリング結果を取得
			importVerticesFromFile(m, g, timestamp);
		}

		long t2 = System.currentTimeMillis();
		// System.out.println("[TIME] for clustering: " + (t2-t1) + " clusterSize=" +
		// g.clustersizeRatio);

		long t3 = System.currentTimeMillis();

		// Calculate distances between vertices
		calcDistancesForLayout(m, g);

		// Calculate initial positions of vertices
		// レイアウトの前半
		// InitialLayoutInvoker.exec(g, m);
		InitialLayoutInvoker.execWithoutForceDirected(g, m);

		long t4 = System.currentTimeMillis();
		// System.out.println("[TIME] for force-directed: " + (t4-t3));

		// Delaunay triangulation
		// レイアウトの後半の準備 -> 後半は MeshSmoother.smooth
		MeshTriangulator.triangulate(m);

		// for test
		printStatistics(m, g);

		return m;
	}

	/**
	 * ファイルからクラスタリング結果を取得
	 * (csvファイルの 0 行目は vertex 0 に属するnodeのid)
	 * 
	 * @param mesh
	 * @param graph
	 * @param timestamp dynamic graphのタイムスタンプ
	 */
	public static void importVerticesFromFile(Mesh mesh, Graph graph, int timestamp) {
		mesh.vertices.clear();

		final String filename = dataset.getComsPath()
				+ "runDynamicModularity_" + dataset.getName() + "_com_" + timestamp + "_nodes.csv";

		try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
			String line;
			while ((line = reader.readLine()) != null) {
				// 新しいメタノードの追加
				final Vertex vertex = mesh.addOneVertex();

				// ファイルの内容に従って、メタノードに属するnodeを追加
				String[] node_ids = line.split(",");
				for (String node_id : node_ids) {
					final Node node = graph.getNode(Integer.parseInt(node_id));
					vertex.nodes.add(node);
					node.setVertex(vertex);
				}
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	/**
	 * Generate vertices
	 * ここでは、1つのVertex(メタノード)に1つのnodeが属する
	 */
	public static void generateVertices(Mesh mesh, Graph graph) {
		mesh.vertices.clear();

		// for each node of the graph
		for (int i = 0; i < graph.nodes.size(); i++) {
			Node node = (Node) graph.nodes.get(i);
			Vertex vertex = mesh.addOneVertex();
			vertex.nodes.add(node);
			node.setVertex(vertex);
			vertex.setPosition(node.getX(), node.getY(), 0.0);
		}

		numvThreshold = (int) ((1.0 - clustersizeRatio) * (double) graph.nodes.size());
		if (numvThreshold < 2)
			numvThreshold = 2;
	}

	/**
	 * Cluster vertices
	 */
	public static void clusterVertices(Mesh mesh, Graph graph) {

		graph.setupDissimilarityForClustering();
		for (int i = 0; i < clusteringMaxIteration; i++) {
			double threshold = clusterVerticesOneStep(mesh);
			// System.out.println(" numnode=" + graph.nodes.size() + " numvertex=" +
			// mesh.getNumVertices() + " th=" + threshold + " maxnumv=" + numvThreshold);
			// if(threshold > graph.clustersizeRatio) break;
			if (mesh.vertices.size() <= numvThreshold)
				break;
		}

	}

	/**
	 * One step of the vertex clustering
	 */
	static double clusterVerticesOneStep(Mesh mesh) {

		// for each pair of the vertices
		double mindis = 1.0e+30;
		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex v1 = mesh.getVertex(i);
			for (int j = (i + 1); j < mesh.getNumVertices(); j++) {
				Vertex v2 = mesh.getVertex(j);

				// for each pair of the nodes
				double maxdis = 0.0;
				for (int ii = 0; ii < v1.nodes.size(); ii++) {
					Node n1 = (Node) v1.nodes.get(ii);
					for (int jj = 0; jj < v2.nodes.size(); jj++) {
						Node n2 = (Node) v2.nodes.get(jj);
						if (n1.getDisSim2(n2.getId()) > maxdis) {
							maxdis = n1.getDisSim2(n2.getId());
							if (maxdis > mindis) {
								ii = v1.nodes.size();
								break;
							}
						}
					}
				}

				// update mindis
				if (mindis > maxdis) {
					mindis = maxdis;
					// System.out.println(" updated mindis=" + mindis);
				}
			}
		}

		// Determine the threshold
		double threshold = mindis * clusteringThreshold;

		// Combine close two vertices
		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex v1 = mesh.getVertex(i);
			for (int j = (i + 1); j < mesh.getNumVertices(); j++) {
				Vertex v2 = mesh.getVertex(j);

				// for each pair of the nodes
				double maxdis = -1.0;
				for (int ii = 0; ii < v1.nodes.size(); ii++) {
					Node n1 = (Node) v1.nodes.get(ii);
					for (int jj = 0; jj < v2.nodes.size(); jj++) {
						Node n2 = (Node) v2.nodes.get(jj);
						if (n1.getDisSim2(n2.getId()) > maxdis) {
							maxdis = n1.getDisSim2(n2.getId());
							if (maxdis > threshold) {
								ii = v1.nodes.size();
								break;
							}
						}
					}
				}
				if (maxdis > threshold)
					continue;

				// System.out.println(" combine: i=" + i + " j=" + j + " names=" + authors + "
				// maxdis=" + maxdis + " th=" + threshold);

				// combine the two vertices
				for (int jj = 0; jj < v2.nodes.size(); jj++) {
					Node n2 = (Node) v2.nodes.get(jj);
					v1.nodes.add(n2);
					n2.setVertex(v1);
				}
				mesh.removeOneVertex(v2);
				j--;
				if (mesh.vertices.size() <= numvThreshold) {
					i = j = mesh.getNumVertices();
					break;
				}
			}
		}

		return threshold;
	}

	/**
	 * Calculate dissimilarity between pairs of vertices
	 */
	public static void calcDistancesForLayout(Mesh mesh, Graph graph) {
		graph.setupDissimilarityForPlacement();
		// Setup an array for dissimilarity calculation
		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex v = mesh.getVertex(i);
			v.dissim = new double[mesh.getNumVertices()];
		}

		// for each pair of the vertices
		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex v1 = mesh.getVertex(i);
			for (int j = (i + 1); j < mesh.getNumVertices(); j++) {
				Vertex v2 = mesh.getVertex(j);

				// calculate inner product
				double dis1 = 0.0;
				if (graph.attributeType == graph.ATTRIBUTE_VECTOR) {
					// ベクトルのコサイン類似度を計算
					double average1[] = new double[graph.vectorname.length];
					double average2[] = new double[graph.vectorname.length];
					for (int k = 0; k < graph.vectorname.length; k++) {
						for (int ii = 0; ii < v1.nodes.size(); ii++) {
							Node n1 = (Node) v1.nodes.get(ii);
							average1[k] += n1.getValue(k);
						}
						for (int ii = 0; ii < v2.nodes.size(); ii++) {
							Node n2 = (Node) v2.nodes.get(ii);
							average2[k] += n2.getValue(k);
						}
					}

					double d1 = 0.0, d2 = 0.0;
					for (int k = 0; k < graph.vectorname.length; k++) {
						dis1 += (average1[k] * average2[k]);
						d1 += (average1[k] * average1[k]);
						d2 += (average2[k] * average2[k]);
					}
					if (dis1 < 0.0)
						dis1 = 0.0;
					else
						dis1 /= (Math.sqrt(d1) * Math.sqrt(d2));
					dis1 = 1.0 - dis1;
				}

				// retrieve distance value
				else if (graph.attributeType == graph.ATTRIBUTE_DISSIM) {
					// 事前に計算された非類似度（dissimilarity）を直接使用
					Node n1 = (Node) v1.nodes.get(0);
					Node n2 = (Node) v2.nodes.get(0);
					dis1 = n1.getDisSim1(n2.getId());
				} else if (graph.attributeType == graph.ATTRIBUTE_COORDINATE_BASED) {
					// 座標ベースの距離計算
					Node n1 = (Node) v1.nodes.get(0);
					Node n2 = (Node) v2.nodes.get(0);
					// ユークリッド距離を計算（getX()とgetY()を使用）
					double dx = n1.getX() - n2.getX();
					double dy = n1.getY() - n2.getY();
					dis1 = Math.sqrt(dx * dx + dy * dy);
					// 正規化（0-1の範囲に収める）
					dis1 = Math.min(1.0, dis1 / 100.0); // 100.0は適切なスケール係数に調整する
				} else if (graph.attributeType == graph.ATTRIBUTE_CLUSTER_BASED) {
					// クラスタベースの距離計算
					Node n1 = (Node) v1.nodes.get(0);
					Node n2 = (Node) v2.nodes.get(0);
					// 同じクラスタ内なら距離を小さく、異なるクラスタなら距離を大きく設定
					dis1 = (n1.getColorId() == n2.getColorId()) ? 0.1 : 1.0;
				} else {

				}

				// for each pair of the nodes belonging to the two vertices
				int count = 0;
				for (int ii = 0; ii < v1.nodes.size(); ii++) {
					Node n1 = (Node) v1.nodes.get(ii);
					for (int jj = 0; jj < v2.nodes.size(); jj++) {
						Node n2 = (Node) v2.nodes.get(jj);
						if (graph.isTwoNodeConnected(n1, n2) == true)
							count++;
					}
				}
				double dis2 = 1.0 / (double) (1 + count);

				// double dis = graph.distanceRatio * dis1 + (1.0 - graph.distanceRatio) * dis2;
				double dis = dis2;
				v1.dissim[j] = v2.dissim[i] = dis;

			}
		}

	}

	static String path = "C:/itot/projects/FRUITSNet/Koala/lib/";
	static String vertex_filename = "polbooks-clustering.txt";
	static int HIERARCHY_LEVEL = 2;

	static void writeEdgeFile(Graph graph) {
		BufferedWriter writer;

		try {
			writer = new BufferedWriter(
					new FileWriter(new File(path + "clusteredges.txt")));
			if (writer == null)
				return;

			for (int i = 0; i < graph.edges.size(); i++) {
				Edge e = graph.edges.get(i);
				Node nodes[] = e.getNode();
				String line = nodes[0].getId() + " " + nodes[1].getId();
				writer.write(line, 0, line.length());
				writer.flush();
				writer.newLine();
			}

			writer.close();

		} catch (Exception e) {
			System.err.println(e);
			writer = null;
			return;
		}

	}

	static int numedgeHisto[] = new int[11];

	/**
	 * Print statistics for test
	 */
	static void printStatistics(Mesh mesh, Graph graph) {

		// System.out.println(" Clustering result: vertices=" + mesh.getNumVertices());

		int sumEdges = 0, sumConnected = 0;
		int sumHubCsize = 0, sumHub = 0;

		for (int i = 0; i < mesh.getNumVertices(); i++) {
			Vertex v1 = mesh.getVertex(i);
			ArrayList<Node> nodes1 = v1.getNodes();
			for (int j = (i + 1); j < mesh.getNumVertices(); j++) {
				Vertex v2 = mesh.getVertex(j);
				ArrayList<Node> nodes2 = v2.getNodes();

				int count = 0;
				for (int ii = 0; ii < nodes1.size(); ii++) {
					Node n1 = nodes1.get(ii);
					for (int jj = 0; jj < nodes2.size(); jj++) {
						Node n2 = nodes2.get(jj);
						if (graph.isTwoNodeConnected(n1, n2) == true)
							count++;
					}
				}
				if (count > 0) {
					sumEdges += count;
					sumConnected++;
					int id = count / 1;
					id = (id > 10) ? 10 : id;
					numedgeHisto[id]++;
				}
			}

			for (int ii = 0; ii < nodes1.size(); ii++) {
				Node n1 = nodes1.get(ii);
				int nc = n1.getNumConnectedEdge() + n1.getNumConnectingEdge();
				if (nc < graph.maxDegree * 0.333333)
					continue;
				sumHub++;
				sumHubCsize += nodes1.size();
			}
		}

		double aveHubCsize = (double) sumHubCsize / (double) sumHub;
		// System.out.println(" ... sumHub=" + sumHub + " aveHubCsize=" + aveHubCsize);

		double aveEdges = (double) sumEdges / (double) sumConnected;
		// System.out.println(" ... sumEdges=" + sumEdges + " aveEdges=" + aveEdges);

		/*
		 * for(int i = 0; i <= 10; i++)
		 * System.out.print(" histo[" + i + "]=" + numedgeHisto[i]);
		 * System.out.println("");
		 */

		/*
		 * int numInEdge = 0;
		 * for(Edge edge : graph.edges) {
		 * Node nodes[] = edge.getNode();
		 * if(nodes[0].getVertex() == nodes[1].getVertex())
		 * numInEdge++;
		 * }
		 * System.out.println("  numInEdge=" + numInEdge);
		 */
	}

}

/*
 * // Apply MDS
 * double[][] output = MDSJ.classicalScaling(input);
 * 
 * // Calculate positions
 * double min1 = +1.0e+30, max1 = -1.0e+30;
 * double min2 = +1.0e+30, max2 = -1.0e+30;
 * for(int i = 0; i < mesh.getNumVertices(); i++) {
 * min1 = (min1 < output[0][i]) ? min1 : output[0][i];
 * max1 = (max1 > output[0][i]) ? max1 : output[0][i];
 * min2 = (min2 < output[1][i]) ? min2 : output[1][i];
 * max2 = (max2 > output[1][i]) ? max2 : output[1][i];
 * }
 * //System.out.println("   min1=" + min1 + " max1=" + max1 + "   min2=" + min2
 * + " max2=" + max2);
 * for(int i = 0; i < mesh.getNumVertices(); i++) {
 * Vertex v = mesh.getVertex(i);
 * double x = ((output[0][i] - min1) / (max1 - min1)) * 2.0 - 1.0;
 * double y = ((output[1][i] - min2) / (max2 - min2)) * 2.0 - 1.0;
 * v.setPosition(x, y, 0.0);
 * for(int j = 0; j < v.nodes.size(); j++) {
 * //System.out.println("     " + j + " x=" + x + " y=" + y);
 * Node n = (Node)v.nodes.get(j);
 * n.setPosition(x, y);
 * }
 * }
 */
