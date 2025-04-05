package ocha.itolab.koala.core.mesh;

import java.util.*;
import ocha.itolab.koala.core.data.*;

/**
 * Vertex
 */
public class Vertex {
	double pos[] = new double[3];
	double color[] = new double[3];
	double radius;
	ArrayList<Node> nodes = new ArrayList<Node>();
	int id;
	double dissim[];
	boolean isForcused = true;
	int meanInDegree = 0;
	int meanOutDegree = 0;
	int dynamicCommunityId = -1;

	public void setId(int id) {
		this.id = id;
	}

	public int getId() {
		return id;
	}

	public void setPosition(double x, double y, double z) {
		pos[0] = x;
		pos[1] = y;
		pos[2] = z;
	}

	public double[] getPosition() {
		return pos;
	}

	public void setColor(double r, double g, double b) {
		color[0] = r;
		color[1] = g;
		color[2] = b;
	}

	public double[] getColor() {
		return color;
	}

	public void setRadius(double r) {
		radius = r;
	}

	public double getRadius() {
		return radius;
	}

	public void addOneNode(Node n) {
		nodes.add(n);
	}

	public ArrayList<Node> getNodes() {
		return nodes;
	}

	public double[] getDissim() {
		return dissim;
	}

	public boolean getIsForcused() {
		return isForcused;
	}

	public void setIsForcusedFalse() {
		isForcused = false;
	}

	public int getMeanInDegree() {
		return meanInDegree;
	}

	public void setMeanInDegree(final int n) {
		meanInDegree = n;
	}

	public int getMeanOutDegree() {
		return meanOutDegree;
	}

	public void setMeanOutDegree(final int n) {
		meanOutDegree = n;
	}

	/**
	 * Return the number of layers of nodes
	 */
	public int getNumNodeLayers() {
		for (int i = 0; i < Mesh.LAYER_NUMNODES.length; i++) {
			if (nodes.size() < Mesh.LAYER_NUMNODES[i])
				return (i + 1);
		}

		return Mesh.LAYER_NUMNODES.length;
	}

	public int getDynamicCommunityId() {
		return dynamicCommunityId;
	}

	public void setDynamicCommunityId(final int id) {
		dynamicCommunityId = id;
	}

}
