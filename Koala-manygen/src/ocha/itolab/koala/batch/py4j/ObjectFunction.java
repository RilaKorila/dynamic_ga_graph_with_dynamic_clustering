package ocha.itolab.koala.batch.py4j;

import py4j.GatewayServer;
import java.util.Map;
import java.util.HashMap;
import java.util.List;

public class ObjectFunction {
	static private Map<String, Map<String, Double>> cache_result = new HashMap<>();

	public double[] obfunc(final int generation, final int id, final double[] previous_gene, final double[] gene,
			final int timestamp, final List<List<Integer>> previousDynamicCommunities,
			final List<List<Integer>> dynamicCommunities) {

		// TimeSmoothnessEvaluator の計算
		final double timeSmoothness = TimeSmoothnessEvaluator.execute(previous_gene, gene,
				timestamp, previousDynamicCommunities, dynamicCommunities);

		// Sprawlter の計算
		// TODO 前のレイアウトは無視して、現在のレイアウトのみSprawlterで評価する点を再検討する
		final Map<String, Double> sprawlterResults = getSprawlter(generation, id, gene, timestamp);

		final double[] _res = new double[5];
		_res[0] = sprawlterResults.get("sprawl");
		_res[1] = sprawlterResults.get("NN");
		_res[2] = sprawlterResults.get("NE");
		_res[3] = sprawlterResults.get("EE");
		_res[4] = timeSmoothness;

		return _res;
	}

	public void writeCsv(final int generation, final int id, final double[] gene, final int timestamp) {
		KoalaToSprawlter.writeLayoutFile(gene, generation, id, timestamp);
	}

	private Map<String, Double> getSprawlter(final int generation, final int id, final double[] gene,
			final int timestamp) {
		Map<String, Double> sprawlterResultMap = new HashMap<>();

		// もしすでに計算済みなら計算結果を返す
		if (cache_result.containsKey(generation + "-" + id)) {
			sprawlterResultMap = cache_result.get(generation + "-" + id);
		} else {
			// execute KoalaToSprawlter
			sprawlterResultMap = KoalaToSprawlter.execute(gene, timestamp); // Experiment 1-S
			// results_map = KoalaToSprawlterOfForcusedVertex.execute(_arr);
			cache_result.put(generation + "-" + id, sprawlterResultMap);
		}

		sprawlterResultMap = KoalaToSprawlter.execute(gene, timestamp); // Experiment 1-S
		// results_map = KoalaToSprawlterOfForcusedVertex.execute(_arr);
		cache_result.put(generation + "-" + id, sprawlterResultMap);
		return sprawlterResultMap;
	}

	public static void main(String[] args) {
		ObjectFunction app = new ObjectFunction();
		GatewayServer server = new GatewayServer(app);
		server.start();
		System.out.println("Gateway Server Started");
	}
}
