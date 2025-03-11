package ocha.itolab.koala.core;

import ocha.itolab.koala.core.data.*;
import ocha.itolab.koala.core.mesh.MeshSmoother;
import ocha.itolab.koala.core.mesh.MeshTriangulator;

public class ManyLayoutGenerator {
	static int ITERATION = 16000;
	
	public static void main(String args[]) {
		String path = "C:/itot/projects/GraphVis/Koala/Koala-manygen/";
		// String inputfilename = path + "NBAF_Coauthorship_12dim-300nodes.csv";
		String inputfilename = path + "cleaned_NBAF_Coauthorship_12dim-300nodes.csv";
		// System.out.println("read input data file");
		
		
		// Repeat generating layouts
		for(int i = 0; i < ITERATION; i++){

			// Read graph file
			Graph graph = GraphFileReader.readConnectivity(inputfilename);
			graph.generateEdges();
			
			// Smoothing
			double idealDistance = 0.05 * (0.5 + 3.0 * Math.random());		
			for(int j = 0; j < 10000; j++) {
				MeshTriangulator.triangulate(graph.mesh);
				boolean ret = MeshSmoother.smooth(graph.mesh, graph.maxDegree, idealDistance);
			}
			
			// Finalize
			graph.mesh.finalizePosition();
			
			// Write the layout file
			String outfilename = path + "result/layout" + i + ".csv";
			LayoutFileWriter.write(graph, outfilename);
		}
		
	}
	
}
