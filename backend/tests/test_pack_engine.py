from app.services.pack_engine import LIQUID, NORMAL, PRINTED, StopItem, pack_route


def test_packs_in_route_order_splitting_bags():
    stops = [
        StopItem(1, 1, 2.0, 3.0),
        StopItem(2, 2, 2.5, 3.0),
        StopItem(3, 3, 1.0, 1.0),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2, 3]
    assert not result.rejects


def test_reject_oversized_stop():
    stops = [StopItem(1, 1, 9.0, 1.0, "大件"), StopItem(2, 2, 1.0, 1.0)]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    assert result.rejects[0][0].stop_id == 1
    assert len(result.bags) == 1
    assert result.bags[0].items[0].stop_id == 2


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2


def test_printed_and_liquid_never_share_bag_even_with_capacity_left():
    # 三件合计 3kg/3L，双约束本可同袋，但印刷与液体必须逐件新开袋
    stops = [
        StopItem(1, 1, 1.0, 1.0, "印刷甲", PRINTED),
        StopItem(2, 2, 1.0, 1.0, "液体甲", LIQUID),
        StopItem(3, 3, 1.0, 1.0, "印刷乙", PRINTED),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=10.0)
    assert not result.rejects
    assert len(result.bags) == 3
    for bag in result.bags:
        cats = {i.category for i in bag.items}
        assert not (PRINTED in cats and LIQUID in cats)
    # 印刷在前、液体紧随相邻，重量体积仍够却被互斥拆开
    first = result.bags[0]
    liquid_item = next(i for i in stops if i.stop_id == 2)
    assert first.weight_kg + liquid_item.weight_kg <= 10.0
    assert first.volume_l + liquid_item.volume_l <= 10.0
    assert liquid_item.stop_id not in [i.stop_id for i in first.items]


def test_normal_adjacent_can_share_bag_with_printed():
    stops = [
        StopItem(1, 1, 1.0, 1.0, "普通甲", NORMAL),
        StopItem(2, 2, 1.0, 1.0, "印刷甲", PRINTED),
        StopItem(3, 3, 1.0, 1.0, "普通乙", NORMAL),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=10.0)
    assert len(result.bags) == 1
    assert [i.stop_id for i in result.bags[0].items] == [1, 2, 3]


def test_normal_can_share_bag_with_liquid():
    stops = [
        StopItem(1, 1, 1.0, 1.0, "液体甲", LIQUID),
        StopItem(2, 2, 1.0, 1.0, "普通甲", NORMAL),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=10.0)
    assert len(result.bags) == 1
    assert [i.stop_id for i in result.bags[0].items] == [1, 2]


def test_oversized_liquid_stop_still_rejected():
    # 单站超限与品类无关：液体大件直接拒收，前后印刷品可同袋
    stops = [
        StopItem(1, 1, 1.0, 1.0, "印刷甲", PRINTED),
        StopItem(2, 2, 9.0, 1.0, "液体大件", LIQUID),
        StopItem(3, 3, 1.0, 1.0, "印刷乙", PRINTED),
    ]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert [r[0].stop_id for r in result.rejects] == [2]
    assert "超重" in result.rejects[0][1]
    assert len(result.bags) == 1
    assert [i.stop_id for i in result.bags[0].items] == [1, 3]


def test_seed_scenario_adjacent_printed_liquid_split_normal_joins():
    # 对应种子城东晨线（8kg / 18L）：seq2 印刷与 seq3 液体相邻，
    # 双约束本可同袋，但互斥强制新开；普通品可分别并入两袋；超限站仍拒。
    stops = [
        StopItem(1, 1, 2.2, 4.0, "松林里 3 栋", NORMAL),
        StopItem(2, 2, 1.8, 3.0, "地铁口快递柜", PRINTED),
        StopItem(3, 3, 2.0, 4.5, "咖啡店后门", LIQUID),
        StopItem(4, 4, 3.5, 5.5, "梧桐苑门岗", NORMAL),
        StopItem(5, 5, 9.5, 6.0, "超大件样例", NORMAL),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)

    bag1, bag2 = result.bags
    assert [i.stop_id for i in bag1.items] == [1, 2]
    assert [i.stop_id for i in bag2.items] == [3, 4]
    # 液体（seq3）若放进袋1，重量 6.0kg、体积 11.5L 均不超限——拆袋纯粹因为互斥
    assert bag1.weight_kg + 2.0 <= 8.0
    assert bag1.volume_l + 4.5 <= 18.0
    for bag in result.bags:
        cats = {i.category for i in bag.items}
        assert not (PRINTED in cats and LIQUID in cats)
    assert [r[0].stop_id for r in result.rejects] == [5]
