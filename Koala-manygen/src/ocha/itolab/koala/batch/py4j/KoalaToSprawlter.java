package ocha.itolab.koala.batch.py4j;

import java.util.ArrayList;
import ocha.itolab.koala.constants.ResourceFile;
import ocha.itolab.koala.core.data.*;
import ocha.itolab.koala.core.forcedirected.LinLogLayout;
import ocha.itolab.koala.core.mesh.*;
import ocha.itolab.koala.evaluate.sprawlter.*;
import java.util.Map;
import java.util.HashMap;

public class KoalaToSprawlter {
	static String infile = ResourceFile.DATA_CSV.path();
	static String outfiledir = ResourceFile.RESULT.path();
	static Graph graph;
	static int SMOOTHING_ITERATION = 100;
	static int NUM_PER_GENERATION = 20;

	static double NN_RATIO = 1.0, NE_RATIO = 1.0, EE_RATIO = 0.5;

	/**
	 * Execute Koala and Sprawlter
	 */
	public static Map<String, Double> execute(double init[]) {
		System.out.println("Forcus条件適用なし");

		// double List から LinLogLayoutクラスのinitialPosに変換
		generateInitPositionList(init);

		// ---------- initial positionに基づいてグラフを生成 ----------
		graph = GraphFileReader.readConnectivity(infile);
		graph.generateEdges();
		for (int i = 0; i < SMOOTHING_ITERATION; i++) {
			// ドロネー三角法を適用
			MeshTriangulator.triangulate(graph.mesh);
			// ラプラシアンスムーザーを適用
			MeshSmoother.smooth(graph.mesh, graph.maxDegree, 0.05);
		}
		graph.mesh.finalizePosition();

		// writeLayoutFile(graph);

		// ---------- 生成したグラフの評価 ----------
		SprawlterEvaluator.preprocess(graph);
		SprawlterEvaluator.calcNodeNodePenalty(graph, 1);
		SprawlterEvaluator.calcNodeEdgePenalty(graph, 1);

		// Sprawlの算出式
		double sprawl = SprawlterEvaluator.calcSprawl(graph);
		System.out.println(String.format("sprawl: %f", sprawl));

		double nnpen = SprawlterEvaluator.calcNodeNodePenalty(graph, 2);
		double nepen = SprawlterEvaluator.calcNodeEdgePenalty(graph, 2);
		double eepen = SprawlterEvaluator.calcEdgeEdgePenalty(graph);

		// nnpen = Math.sqrt(sprawl * nnpen / nnmax);
		// nepen = Math.sqrt(sprawl * nepen / nemax);
		// eepen = Math.sqrt(sprawl * eepen / eemax);
		System.out.println(String.format("nnpen: %f, nepen: %f, eepen: %f", nnpen, nepen, eepen));

		double sprawlter = NN_RATIO * nnpen + NE_RATIO * nepen + EE_RATIO * eepen;
		System.out.println(String.format("--------- %f ", sprawlter));

		// sprawl, NN, NE, EE 全てを返す
		Map<String, Double> results = new HashMap<String, Double>();
		results.put("sprawl", sprawl);
		results.put("NN", nnpen);
		results.put("NE", nepen);
		results.put("EE", eepen);

		return results;
	}

	static void generateInitPositionList(double init[]) {
		ArrayList<double[]> poslist = new ArrayList<double[]>();
		for (int i = 0; i < init.length; i += 2) {
			double pos[] = new double[3];
			pos[0] = init[i] * 0.1;
			pos[1] = init[i + 1] * 0.1;
			pos[2] = 0.0;
			poslist.add(pos);
		}
		LinLogLayout.setInitialPositionList(poslist);
	}

	static void writeLayoutFile(double init[], Integer generation, Integer id) {
		String filename = outfiledir + "/layout" + generation + "-" + id + ".csv";

		// double List から LinLogLayoutクラスのinitialPosに変換
		generateInitPositionList(init);

		// ---------- initial positionに基づいてグラフを生成 ----------
		graph = GraphFileReader.readConnectivity(infile);
		graph.generateEdges();
		for (int i = 0; i < SMOOTHING_ITERATION; i++) {
			// ドロネー三角法を適用
			MeshTriangulator.triangulate(graph.mesh);
			// ラプラシアンスムーザーを適用
			MeshSmoother.smooth(graph.mesh, graph.maxDegree, 0.05);
		}
		graph.mesh.finalizePosition();

		try {
			LayoutFileWriter.write(graph, filename);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
}
