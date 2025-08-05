package ocha.itolab.koala.batch.py4j;

import ocha.itolab.koala.core.mesh.Vertex;
import ocha.itolab.koala.core.data.Node;
import ocha.itolab.koala.core.data.Graph;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.AbstractMap;
import java.util.stream.Collectors;

public class TimeSmoothnessEvaluator {
    public TimeSmoothnessEvaluator() {
    }

    public static double execute(final double previousInit[], final double init[], final int timestamp,
            final List<List<Integer>> previousDynamicCommunities, final List<List<Integer>> dynamicCommunities,
            final Map<Integer, List<AbstractMap.SimpleEntry<Integer, Double>>> similarCommunities) {
        if (previousDynamicCommunities == null) {
            return 0.0;
        }

        // ノードIDのリストをキー、動的コミュニティIDを値とするマッピングを作成
        final HashMap<List<Integer>, Integer> dynamicCommunityIdMap = getDynamicCommunityIdMap(dynamicCommunities);
        final Graph currentGraph = KoalaToSprawlter.getGraph(init, timestamp);
        // GraphのVertex(メタノード)に動的コミュニティIDを割り当てる
        assignDynamicCommunityId(currentGraph, dynamicCommunityIdMap);

        // 1つ前のタイムスタンプでも同様の処理を行う
        final HashMap<List<Integer>, Integer> previousDynamicCommunityIdMap = getDynamicCommunityIdMap(
                previousDynamicCommunities);
        final Graph previousGraph = KoalaToSprawlter.getGraph(previousInit, timestamp - 1);
        assignDynamicCommunityId(previousGraph, previousDynamicCommunityIdMap);

        // 時間平滑性を計算する
        return calculateTimeSmoothnessWithMultipleMatches(previousGraph, currentGraph, similarCommunities);
    }

    /**
     * Vertex(つまりメタノード)に動的コミュニティIDを割り当てる
     * 
     * @param graph                 グラフ
     * @param dynamicCommunityIdMap ノードリストと動的コミュニティIDのマッピング
     */
    private static void assignDynamicCommunityId(final Graph graph,
            final HashMap<List<Integer>, Integer> dynamicCommunityIdMap) {
        for (Vertex vertex : graph.mesh.getVertices()) {
            // Nodeのリストを文字列のリストに変換
            final List<Integer> nodeIds = vertex.getNodes().stream()
                    .map(Node::getId)
                    .sorted()
                    .collect(Collectors.toList());
            Integer dynamicCommunityId = dynamicCommunityIdMap.get(nodeIds);

            if (dynamicCommunityId == null) {
                System.out.println("読み込むデータセットが正しいか要確認");
                System.out.println("Warning: No community found for nodes: " + nodeIds);
                continue;
            }
            vertex.setDynamicCommunityId(dynamicCommunityId);
        }
    }

    /**
     * ノードリストと動的コミュニティIDのマッピングを作成する
     * 
     * @param nodes
     * @param dynamicCommunities
     * @return ノードリストがキー、動的コミュニティIDが値のマッピング
     */
    private static HashMap<List<Integer>, Integer> getDynamicCommunityIdMap(
            final List<List<Integer>> dynamicCommunities) {
        final HashMap<List<Integer>, Integer> dynamicCommunityIdMap = new HashMap<>(dynamicCommunities.size());

        for (int i = 0; i < dynamicCommunities.size(); i++) {
            final List<Integer> nodeIds = dynamicCommunities.get(i).stream()
                    .sorted().toList();
            dynamicCommunityIdMap.put(nodeIds, i);
        }

        return dynamicCommunityIdMap;
    }

    /**
     * 時間平滑性を計算する
     * 
     * @param previousGraph 1つ前のタイムスタンプのグラフ
     * @param currentGraph  現在のタイムスタンプのグラフ
     * @return 時間平滑性
     */
    private static double calculateTimeSmoothness(final Graph previousGraph, final Graph currentGraph) {
        double totalDistance = 0.0;

        for (Vertex currentVertex : currentGraph.mesh.getVertices()) {
            for (Vertex previousVertex : previousGraph.mesh.getVertices()) {

                // 同じDynamicCommunityに属しているかどうかを判断
                if (currentVertex.getDynamicCommunityId() == previousVertex.getDynamicCommunityId()) {
                    // 大きいmetanodeほどインパクトが大きいので、metanodeに属するnode数を移動距離に乗算する
                    final double penalty = calculateDistance(currentVertex.getPosition(), previousVertex.getPosition(),
                            10.0) * currentVertex.getNodeNum();
                    totalDistance += penalty;
                }
            }
        }

        // TODO
        // Cursorは1つ前のタイムスタンプのグラフのノード数と現在のタイムスタンプのグラフのノード数の比率を用いて、計算しようとしていたので必要かどうかを確認する。
        return totalDistance;
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
