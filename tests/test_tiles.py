from tileplacement.tiles import all_values, mask_el, mask_full, mask_outer_boundary


def test_all_values_contains_expected_domain_values():
    vals = set(all_values())
    assert ("FULL_BLOCK", 0) in vals
    assert ("OUTER_BOUNDARY", 0) in vals
    for rot in range(4):
        assert ("EL_SHAPE", rot) in vals
    assert len(vals) == 6


def test_full_block_covers_all_cells():
    m = mask_full()
    assert len(m) == 4
    assert all(len(row) == 4 for row in m)
    assert all(cell for row in m for cell in row)


def test_outer_boundary_mask_shape():
    m = mask_outer_boundary()
    for r in range(4):
        for c in range(4):
            expected = r in (0, 3) or c in (0, 3)
            assert m[r][c] is expected


def test_el_rotations_match_spec():
    m0 = mask_el(0)
    assert all(m0[0][c] for c in range(4))
    assert all(m0[r][0] for r in range(4))

    m1 = mask_el(1)
    assert all(m1[0][c] for c in range(4))
    assert all(m1[r][3] for r in range(4))

    m2 = mask_el(2)
    assert all(m2[3][c] for c in range(4))
    assert all(m2[r][3] for r in range(4))

    m3 = mask_el(3)
    assert all(m3[3][c] for c in range(4))
    assert all(m3[r][0] for r in range(4))
