package ocha.itolab.koala.batch.py4j;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import ocha.itolab.koala.constants.ResourceFile;
import ocha.itolab.koala.core.data.*;
import ocha.itolab.koala.core.forcedirected.LinLogLayout;
import ocha.itolab.koala.core.mesh.*;
import ocha.itolab.koala.evaluate.sprawlter.*;
import java.util.Map;
import java.util.HashMap;

public class KoalaToSprawlter {
	// NBAF_Coauthorship_12dim.csvを読み込む
	// static String infile = ResourceFile.DATA_CSV.path();
	// Cit-HepPhのデータを読み込む
	static Graph graph;
	static int SMOOTHING_ITERATION = 100;
	static int NUM_PER_GENERATION = 20;

	static double NN_RATIO = 1.0, NE_RATIO = 1.0, EE_RATIO = 0.5;

	/**
	 * Execute Koala and Sprawlter
	 */
	public static Map<String, Double> execute(final double init[], final int timestamp) {
		System.out.println("Forcus条件適用なし");

		graph = getGraph(init, timestamp);

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

	public static Graph getGraph(final double init[], final int timestamp) {
		// Cit-HepPhのデータを読み込む
		// final String infile = ResourceFile.CIT_HEP_PH_DATA_DIR.path() + "connectivity_timestamp_" + timestamp + ".csv";
		final String infile = ResourceFile.FACEBOOK_DATA_DIR.path() + "connectivity_timestamp_" + timestamp + ".csv";

		// double List から LinLogLayoutクラスのinitialPosに変換
		generateInitPositionList(init);

		// ---------- initial positionに基づいてグラフを生成 ----------
		graph = GraphFileReader.readConnectivity(infile, timestamp);
		graph.generateEdges();
		for (int i = 0; i < SMOOTHING_ITERATION; i++) {
			// ドロネー三角法を適用
			MeshTriangulator.triangulate(graph.mesh);
			// ラプラシアンスムーザーを適用
			MeshSmoother.smooth(graph.mesh, graph.maxDegree, 0.05);
		}
		graph.mesh.finalizePosition();

		return graph;
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

	static void writeLayoutFile(double init[], int timestamp, final String fname) {
		final String dirName = createDirectory(ResourceFile.RESULT.path() + "/" + timestamp + "/");
		final String filePath = dirName + fname;

		graph = getGraph(init, timestamp);

		try {
			LayoutFileWriter.write(graph, filePath);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * ディレクトリが存在していなければ作成する
	 * 
	 * @param dirName ディレクトリのパス
	 * @return ディレクトリのパス
	 */
	private static String createDirectory(final String dirName) {
		new File(dirName).mkdirs();
		return dirName;
	}

}
