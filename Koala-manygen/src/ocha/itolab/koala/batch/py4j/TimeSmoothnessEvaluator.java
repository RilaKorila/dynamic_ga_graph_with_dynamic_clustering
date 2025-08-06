package ocha.itolab.koala.batch.py4j;

import ocha.itolab.koala.core.mesh.Vertex;
import ocha.itolab.koala.core.data.Graph;

import java.util.Map;
import java.util.List;
import java.util.AbstractMap;

public class TimeSmoothnessEvaluator {
    public TimeSmoothnessEvaluator() {
    }

    public static double execute(final double previousInit[], final double init[], final int timestamp,
            final Map<Integer, List<AbstractMap.SimpleEntry<Integer, Double>>> similarCommunities) {
        if (previousInit == null) {
            return 0.0;
        }

        final Graph currentGraph = KoalaToSprawlter.getGraph(init, timestamp);

        // 1つ前のタイムスタンプでも同様の処理を行う
        final Graph previousGraph = KoalaToSprawlter.getGraph(previousInit, timestamp - 1);

        // 時間平滑性を計算する
        return calculateTimeSmoothnessWithMultipleMatches(previousGraph, currentGraph, similarCommunities);
    }

    /**
     * 時間平滑性を計算する。similarCommunitiesを使用して類似コミュニティ間の距離を計算する。
     * 
     * @param previousGraph      1つ前のタイムスタンプのグラフ
     * @param currentGraph       現在のタイムスタンプのグラフ
     * @param similarCommunities 類似コミュニティのマッピング
     * @return 時間平滑性
     */
    private static double calculateTimeSmoothnessWithMultipleMatches(final Graph previousGraph,
            final Graph currentGraph,
            final Map<Integer, List<AbstractMap.SimpleEntry<Integer, Double>>> similarCommunities) {
        double totalDistance = 0.0;

        // similarCommunities でループ
        for (final int currentCommunityId : similarCommunities.keySet()) {
            final List<AbstractMap.SimpleEntry<Integer, Double>> similarCommunitiesList = similarCommunities
                    .get(currentCommunityId);
            for (final AbstractMap.SimpleEntry<Integer, Double> similarCommunity : similarCommunitiesList) {
                final int previousCommunityId = similarCommunity.getKey();
                final double similarity = similarCommunity.getValue();

                // 類似コミュニティに属する前のグラフの頂点を探す
                final Vertex previousVertex = previousGraph.mesh.getVertex(previousCommunityId);
                final Vertex currentVertex = currentGraph.mesh.getVertex(currentCommunityId);

                double penalty = calculateDistance(
                        currentVertex.getPosition(),
                        previousVertex.getPosition(), 1) * currentVertex.getNodeNum() * similarity;
                totalDistance += penalty;
            }
        }

        // TODO
        // Cursorは1つ前のタイムスタンプのグラフのノード数と現在のタイムスタンプのグラフのノード数の比率を用いて、計算しようとしていたので必要かどうかを確認する。
        return totalDistance;
    }

    /**
     * 2点間のユークリッド距離を計算する
     * 
     * @param p1    点1の座標
     * @param p2    点2の座標
     * @param scale 座標が1以下の場合、ユークリッド距離を取ると小さくなり過ぎてしまうのでscaleで等倍処理する
     * @return 2点間のユークリッド距離
     */
    private static double calculateDistance(final double[] p1, final double[] p2, final double scale) {
        double dx = Math.abs(p1[0] - p2[0]) * scale;
        double dy = Math.abs(p1[1] - p2[1]) * scale;

        double distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < 1e-6)
            distance = 0.0;
        return distance;
    }

}
