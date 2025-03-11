package ocha.itolab.koala.batch.py4j;

import py4j.GatewayServer;
import java.util.Map;
import java.util.HashMap;
import java.util.List;

public class ObjectFunction {
	static private Map<String, Map<String, Double>> cache_result = new HashMap<>();
	private double[] _arr; // Experiment 1-S
	private double[] _result = new double[4];

	// 遺伝子の長さを設定(python側から呼び出される)
	public void set_gene_length(int length) {
		_arr = new double[length];
	}

	public double[] obfunc(int generation, int id, double val, int current, int finish) {
		// store values
		_arr[current] = val;

		if (current == finish - 1) {
			Map<String, Double> results_map = new HashMap<>();
			// もしすでに計算済みなら計算結果を返す
			if (cache_result.containsKey(generation + "-" + id)) {
				results_map = cache_result.get(generation + "-" + id);
			} else {
				// execute KoalaToSprawlter
				results_map = KoalaToSprawlter.execute(_arr); // Experiment 1-S
				// results_map = KoalaToSprawlterOfForcusedVertex.execute(_arr);
				cache_result.put(generation + "-" + id, results_map);
			}

			_result[0] = results_map.get("sprawl");
			_result[1] = results_map.get("NN");
			_result[2] = results_map.get("NE");
			_result[3] = results_map.get("EE");
		}

		return _result;
	}

	public void writeCsv(int generation, int id, double val, int current, int finish) {
		// store values
		_arr[current] = val;

		if (current == finish - 1) {
			KoalaToSprawlterOfForcusedVertex.writeLayoutFile(_arr, generation, id);
		}
	}

	public static void main(String[] args) {
		ObjectFunction app = new ObjectFunction();
		GatewayServer server = new GatewayServer(app);
		server.start();
		System.out.println("Gateway Server Started");
	}
}
