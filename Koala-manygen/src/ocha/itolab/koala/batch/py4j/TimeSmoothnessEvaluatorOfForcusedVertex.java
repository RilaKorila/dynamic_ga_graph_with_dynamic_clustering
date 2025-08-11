package ocha.itolab.koala.batch.py4j;

import ocha.itolab.koala.core.mesh.Vertex;
import ocha.itolab.koala.core.data.Graph;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.AbstractMap;

public class TimeSmoothnessEvaluatorOfForcusedVertex {
    public TimeSmoothnessEvaluatorOfForcusedVertex() {
    }

    public static double execute(final double previousInit[], final double init[], final int timestamp,
            final List<List<Integer>> previousDynamicCommunities, final List<List<Integer>> dynamicCommunities,
            final Map<Integer, List<AbstractMap.SimpleEntry<Integer, Double>>> similarCommunities) {

        if (previousDynamicCommunities == null) {
            return 0.0;
        }

        // ノードIDのリストをキー、動的コミュニティIDを値とするマッピングを作成
        final HashMap<List<Integer>, Integer> dynamicCommunityIdMap = TimeSmoothnessEvaluator.getDynamicCommunityIdMap(
                dynamicCommunities);
        final Graph currentGraph = KoalaToSprawlter.getGraph(init, timestamp);
        // GraphのVertex(メタノード)に動的コミュニティIDを割り当てる
        TimeSmoothnessEvaluator.assignDynamicCommunityId(currentGraph, dynamicCommunityIdMap);

        // 1つ前のタイムスタンプでも同様の処理を行う
        final HashMap<List<Integer>, Integer> previousDynamicCommunityIdMap = TimeSmoothnessEvaluator
                .getDynamicCommunityIdMap(
                        previousDynamicCommunities);
        final Graph previousGraph = KoalaToSprawlter.getGraph(previousInit, timestamp - 1);
        // GraphのVertex(メタノード)に動的コミュニティIDを割り当てる
        TimeSmoothnessEvaluator.assignDynamicCommunityId(previousGraph, previousDynamicCommunityIdMap);
        // 時間平滑性を計算する
        return calculateTimeSmoothnessOfForcusedVertex(previousGraph, currentGraph);
    }

    /**
     * 時間平滑性を計算する
     * 
     * @param previousGraph 1つ前のタイムスタンプのグラフ
     * @param currentGraph  現在のタイムスタンプのグラフ
     * @return 時間平滑性
     */
    private static double calculateTimeSmoothnessOfForcusedVertex(final Graph previousGraph, final Graph currentGraph) {
        double totalDistance = 0.0;

        for (Vertex currentVertex : currentGraph.mesh.getVertices()) {

            // Forcus対象のVetexではない場合は計算しない
            if (!currentVertex.getIsForcused())
                continue;

            for (Vertex previousVertex : previousGraph.mesh.getVertices()) {

                // Forcus対象のVetexではない場合は計算しない
                if (!previousVertex.getIsForcused())
                    continue;

                // 同じDynamicCommunityに属しているかどうかを判断
                if (currentVertex.getDynamicCommunityId() == previousVertex.getDynamicCommunityId()) {
                    // 大きいmetanodeほどインパクトが大きいので、metanodeに属するnode数を移動距離に乗算する
                    final double penalty = TimeSmoothnessEvaluator.calculateDistance(currentVertex.getPosition(),
                            previousVertex.getPosition(), 10.0) * currentVertex.getNodeNum();
                    totalDistance += penalty;
                }
            }
        }

        // TODO
        // Cursorは1つ前のタイムスタンプのグラフのノード数と現在のタイムスタンプのグラフのノード数の比率を用いて、計算しようとしていたので必要かどうかを確認する。
        return totalDistance;
    }
}
