package ocha.itolab.koala.core.data;

public class Edge {
	int id;
	Node nodes[] = new Node[2];	
	
	public void setNode(Node n1, Node n2) {
		nodes[0] = n1;
		nodes[1] = n2;
	}
	
	public Node[] getNode() {
		return nodes;
	}
	
}
