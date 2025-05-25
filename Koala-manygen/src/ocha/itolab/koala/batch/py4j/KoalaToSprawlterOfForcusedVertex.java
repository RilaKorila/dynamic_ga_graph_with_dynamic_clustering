package ocha.itolab.koala.batch.py4j;

import java.io.File;
import java.util.ArrayList;

import ocha.itolab.koala.constants.Dataset;
import ocha.itolab.koala.constants.ResourceFile;
import ocha.itolab.koala.core.data.*;
import ocha.itolab.koala.core.forcedirected.LinLogLayout;
import ocha.itolab.koala.core.mesh.*;
import ocha.itolab.koala.evaluate.sprawlter.*;
import java.util.Map;
import java.util.HashMap;

public class KoalaToSprawlterOfForcusedVertex {
	// NBAF_Coauthorship_12dim.csvを読み込む
	// static String infile = ResourceFile.DATA_CSV.path();
	static Graph graph;
	static int SMOOTHING_ITERATION = 100;
	static int NUM_PER_GENERATION = 20; // 個体数
	static Dataset dataset = Dataset.CIT_HEP_PH;

	/**
	 * Execute Koala and Sprawlter
	 */
	public static Map<String, Double> execute(final double init[], final int timestamp) {
		// Cit-HepPhのデータを読み込む
		final String infile = dataset.getDataDirPath() + "connectivity_timestamp_" + timestamp + ".csv";

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

		// writeLayoutFile(graph);

		// ---------- 生成したグラフの評価 ----------
		SprawlterEvaluator.preprocess(graph);
		SprawlterEvaluator.calcNodeNodePenaltyOfForcusedVertex(graph, 1);
		SprawlterEvaluator.calcNodeEdgePenaltyOfForcusedVertex(graph, 1);

		// Sprawlの算出式
		double sprawl = SprawlterEvaluator.calcSprawlOfForcusedVertex(graph);
		System.out.println(String.format("sprawl: %f", sprawl));

		double nnpen = SprawlterEvaluator.calcNodeNodePenaltyOfForcusedVertex(graph, 2);
		double nepen = SprawlterEvaluator.calcNodeEdgePenaltyOfForcusedVertex(graph, 2);
		System.out.println(String.format("nnpen: %f, nepen: %f", nnpen, nepen));

		// sprawl, NN, NE, EE 全てを返す
		Map<String, Double> results = new HashMap<String, Double>();
		results.put("sprawl", sprawl);
		results.put("NN", nnpen);
		results.put("NE", nepen);
		results.put("EE", 0.0);

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

	public static void writeLayoutFile(double init[], int generation, int id, int timestamp) {
		final String dirName = createDirectory(ResourceFile.RESULT.path() + "/" + timestamp + "/");
		final String filename = dirName + "/layout" + generation + "-" + id + ".csv";

		// データを読み込む
		final String infile = dataset.getDataDirPath() + "connectivity_timestamp_" + timestamp + ".csv";

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

		try {
			LayoutFileWriter.write(graph, filename);
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
