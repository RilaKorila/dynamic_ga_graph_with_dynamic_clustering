package ocha.itolab.koala.core.data;

public class NodeDistanceCalculator {

	static double placeRatio = 0.5, clusteringRatio = 0.5;

	public static void setPlacementRatio(double r) {
		placeRatio = r;
	}

	public static void setClusteringRatio(double r) {
		clusteringRatio = r;
	}

	public static double calcClusteringDistance(Graph g, Node n1, Node n2) {
		double ret = 0.0, ret1 = 0.0;

		if (g.attributeType == g.ATTRIBUTE_VECTOR) {
			double d1 = 0.0, d2 = 0.0;
			for (int i = 0; i < g.vectorname.length; i++) {
				ret1 += (n1.vector[i] * n2.vector[i]); // 内積
				d1 += (n1.vector[i] * n1.vector[i]); // ノード1のベクトルのノルムの二乗
				d2 += (n2.vector[i] * n2.vector[i]); // ノード2のベクトルのノルムの二乗
			}
			if (ret1 < 0.0)
				ret1 = 0.0;
			else {
				double d12 = Math.sqrt(d1) * Math.sqrt(d2);
				if (d12 < 1.0e-8)
					ret1 = 0.0;
				else
					ret1 /= d12; // コサイン類似度を計算
			}
			ret1 = 1.0 - ret1; // 距離に変換（類似度が高いほど距離が小さくなる）
		} else if (g.attributeType == g.ATTRIBUTE_DISSIM) {
			int id2 = n2.getId();
			ret1 = n1.getDisSim1(id2);
		} else if (g.attributeType == g.ATTRIBUTE_COORDINATE_BASED) { // 座標ベース
			double dx = n1.getX() - n2.getX();
			double dy = n1.getY() - n2.getY();
			ret1 = Math.sqrt(dx * dx + dy * dy);
			ret1 = Math.min(1.0, ret1 / 100.0);
		} else if (g.attributeType == g.ATTRIBUTE_CLUSTER_BASED) { // クラスタ情報ベース
			// 同じクラスタであれば、距離を小さく(=0.1)、異なるクラスタであれば、距離を大きく(=1.0) 設定
			ret1 = (n1.getColorId() == n2.getColorId()) ? 0.1 : 1.0;
		} else {
			ret1 = 0.0;
		}

		double ret2 = 0.0;
		int count = 0;
		int num1 = n1.connected.length + n1.connecting.length;
		int num2 = n2.connected.length + n2.connecting.length;
		int id1 = 0, id2 = 0;

		for (int i = 0; i < num1; i++) {
			if (i < n1.connected.length)
				id1 = n1.connected[i];
			else
				id1 = n1.connecting[i - n1.connected.length];

			for (int j = 0; j < num2; j++) {
				if (j < n2.connected.length)
					id2 = n2.connected[j];
				else
					id2 = n2.connecting[j - n2.connected.length];
				if (id1 == id2) {
					count++;
					break;
				}
			}
		}
		int num = num1 + num2;
		if (num <= 0)
			ret2 = 1.0;
		else
			ret2 = (double) (num - count * 2) / (double) num;

		ret = clusteringRatio * ret1 + (1.0 - clusteringRatio) * ret2;

		return ret;
	}

	public static double calcPlacementDistance(Graph g, Node n1, Node n2) {
		double ret = 0.0, ret1 = 0.0;

		if (g.attributeType == g.ATTRIBUTE_VECTOR) {
			double d1 = 0.0, d2 = 0.0;
			for (int i = 0; i < g.vectorname.length; i++) {
				ret1 += (n1.vector[i] * n2.vector[i]);
				d1 += (n1.vector[i] * n1.vector[i]);
				d2 += (n2.vector[i] * n2.vector[i]);
			}
			if (ret1 < 0.0)
				ret1 = 0.0;
			else
				ret1 /= (Math.sqrt(d1) * Math.sqrt(d2));
			ret1 = 1.0 - ret1;
		} else if (g.attributeType == g.ATTRIBUTE_DISSIM) {
			int id2 = n2.getId();
			ret1 = n1.getDisSim1(id2);
		} else {
			ret1 = 0.0;
			// System.out.println("x座標: " + n1.x + ", y座標: " + n1.y);
			// System.out.println("x座標: " + n2.x + ", y座標: " + n2.y);
		}

		boolean isConnected = g.isTwoNodeConnected(n1, n2);
		double ret2 = (isConnected == true) ? 0.0 : 1.0;

		ret = placeRatio * ret1 + (1.0 - placeRatio) * ret2;

		return ret;
	}

}
