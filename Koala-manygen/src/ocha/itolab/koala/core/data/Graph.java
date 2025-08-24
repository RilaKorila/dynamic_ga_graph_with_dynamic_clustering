package ocha.itolab.koala.core.data;

import java.util.*;

import ocha.itolab.koala.core.mesh.*;

public class Graph {
	public int attributeType = -1;
	public int ATTRIBUTE_VECTOR = 1;
	public int ATTRIBUTE_DISSIM = 2;

	// #vectorsタグがあるときは、readVeactor()内で設定される。
	// Koalaでclisteringしない場合はいらない情報なはずなので、別のモードを追加する
	public int ATTRIBUTE_COORDINATE_BASED = 3; // 座標ベースの距離計算を行うモード
	public int ATTRIBUTE_CLUSTER_BASED = 4; // クラスタ情報に基づく距離計算を行うモード

	public String vectorname[];
	public int maxDegree = 0;

	public ArrayList<Node> nodes = new ArrayList<Node>();
	public ArrayList<Edge> edges = new ArrayList<Edge>();
	HashMap<String, Edge> edgemap;
	public Mesh mesh = null;

	public void postprocess(final int timestamp) {
		mesh = MeshGenerator.generate(this, timestamp);
	}

	public void generateEdges() {
		// System.out.println("generateEdges");
		edges.clear();
		edgemap = new HashMap<String, Edge>();

		// for each node
		for (Node node : nodes) {

			// for each node referred node
			if (node.connected != null) {
				for (int j = 0; j < node.connected.length; j++) {
					int connected_node_id = node.connected[j];
					String key = Integer.toString(node.id) + "-" + Integer.toString(connected_node_id);
					Edge e = (Edge) edgemap.get(key);
					if (e == null) {
						e = new Edge();
						e.id = edges.size();
						edges.add(e);
						edgemap.put(key, e);
						final Node node2 = getNode(connected_node_id);
						e.nodes[0] = node;
						e.nodes[1] = node2;
						node.connectedEdge.add(e);
						node2.connectingEdge.add(e);
					}
				}
			}

			// for each node referred node
			if (node.connecting != null) {
				for (int j = 0; j < node.connecting.length; j++) {
					int connecting_node_id = node.connecting[j];
					String key = Integer.toString(connecting_node_id) + "-" + Integer.toString(node.id);
					Edge e = (Edge) edgemap.get(key);
					if (e == null) {
						e = new Edge();
						e.id = edges.size();
						edges.add(e);
						edgemap.put(key, e);
						final Node node2 = getNode(connecting_node_id);
						e.nodes[0] = node2;
						e.nodes[1] = node;
						node2.connectedEdge.add(e);
						node.connectingEdge.add(e);
					}
				}
			}

		}
		// System.out.println("node num: " + Integer.toString(nodes.size()));

		edgemap.clear();

		// Specify the max number of degrees
		maxDegree = 0;
		for (int i = 0; i < nodes.size(); i++) {
			Node node = nodes.get(i);
			int nc = node.getNumConnectedEdge() + node.getNumConnectingEdge();
			maxDegree = (maxDegree < nc) ? nc : maxDegree;
		}

	}

	public void setupDissimilarityForPlacement() {

		// Copy dissimilarity to an allocated array
		for (int i = 0; i < nodes.size(); i++) {
			Node n1 = nodes.get(i);
			n1.dissim2 = new double[nodes.size()];
		}
		for (int i = 0; i < nodes.size(); i++) {
			/*
			 * if(i % 1000 == 0)
			 * System.out.println("   Graph#setupDissimilarityForPlacement " + i);
			 */
			Node n1 = nodes.get(i);
			for (int j = (i + 1); j < nodes.size(); j++) {
				Node n2 = nodes.get(j);
				double d = NodeDistanceCalculator.calcPlacementDistance(this, n1, n2);
				n1.dissim2[j] = n2.dissim2[i] = d;
			}
		}

	}

	public void setupDissimilarityForClustering() {

		// Copy dissimilarity to an allocated array
		for (int i = 0; i < nodes.size(); i++) {
			Node n1 = nodes.get(i);
			n1.dissim2 = new double[nodes.size()];
		}
		for (int i = 0; i < nodes.size(); i++) {
			/*
			 * if(i % 1000 == 0)
			 * System.out.println("   Graph#setupDissimilarityForClustering " + i);
			 */
			Node n1 = nodes.get(i);
			for (int j = (i + 1); j < nodes.size(); j++) {
				Node n2 = nodes.get(j);
				double d = NodeDistanceCalculator.calcClusteringDistance(this, n1, n2);
				n1.dissim2[j] = n2.dissim2[i] = d;
			}
		}

	}

	public boolean isTwoNodeConnected(Node n1, Node n2) {

		for (int i = 0; i < n1.connected.length; i++) {
			int id1 = n1.connected[i];
			if (id1 == n2.id)
				return true;
		}
		for (int i = 0; i < n2.connected.length; i++) {
			int id2 = n2.connected[i];
			if (id2 == n1.id)
				return true;
		}
		for (int i = 0; i < n1.connecting.length; i++) {
			int id1 = n1.connecting[i];
			if (id1 == n2.id)
				return true;
		}
		for (int i = 0; i < n2.connecting.length; i++) {
			int id2 = n2.connecting[i];
			if (id2 == n1.id)
				return true;
		}

		return false;
	}

	/**
	 * ノードIDが合致するノードを取得する
	 * 
	 * @param id ノードのID
	 * @return ノード
	 */
	public Node getNode(int id) {
		// FIXME getNode メソッドが O(n) なのでパフォーマンス劣化あり
		for (int i = 0; i < nodes.size(); i++) {
			if (nodes.get(i).id == id)
				return nodes.get(i);
		}
		return null;
	}

}
