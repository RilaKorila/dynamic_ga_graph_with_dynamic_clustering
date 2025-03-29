package ocha.itolab.koala.batch.py4j;

import py4j.GatewayServer;
import java.util.Map;
import java.util.HashMap;
import java.util.List;

public class ObjectFunction {
	static private Map<String, Map<String, Double>> cache_result = new HashMap<>();
	private double[] _result = new double[4];

	public double[] obfunc(final int generation, final int id, final double[] gene, final int timestamp) {
		Map<String, Double> results_map = new HashMap<>();
		// もしすでに計算済みなら計算結果を返す
		if (cache_result.containsKey(generation + "-" + id)) {
			results_map = cache_result.get(generation + "-" + id);
		} else {
			// execute KoalaToSprawlter
			results_map = KoalaToSprawlter.execute(gene, timestamp); // Experiment 1-S
			// results_map = KoalaToSprawlterOfForcusedVertex.execute(_arr);
			cache_result.put(generation + "-" + id, results_map);
		}

		results_map = KoalaToSprawlter.execute(gene, timestamp); // Experiment 1-S
		// results_map = KoalaToSprawlterOfForcusedVertex.execute(_arr);
		cache_result.put(generation + "-" + id, results_map);

		_result[0] = results_map.get("sprawl");
		_result[1] = results_map.get("NN");
		_result[2] = results_map.get("NE");
		_result[3] = results_map.get("EE");

		return _result;
	}

	public void writeCsv(final int generation, final int id, final double[] gene, final int timestamp) {
		KoalaToSprawlter.writeLayoutFile(gene, generation, id, timestamp);
	}

	public static void main(String[] args) {
		ObjectFunction app = new ObjectFunction();
		GatewayServer server = new GatewayServer(app);
		server.start();
		System.out.println("Gateway Server Started");
	}
}
