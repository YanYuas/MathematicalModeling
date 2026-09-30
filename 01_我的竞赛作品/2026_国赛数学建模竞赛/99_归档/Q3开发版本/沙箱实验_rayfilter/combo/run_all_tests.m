function run_all_tests()
    names = {'test_ray_filter','test_optimize_route','test_clip_to_domain', ...
             'test_sweep_clear','test_phaseC_homing','test_homing_convergence', ...
             'test_clear_source_homing','test_Q1_geometry'};
    pass = 0; fail = {};
    for i = 1:numel(names)
        try
            feval(names{i}); r = true;
            if isempty(r) || (islogical(r) && r)
                fprintf('[OK]   %s\n', names{i}); pass = pass + 1;
            else
                fprintf('[FAIL] %s (返回 false)\n', names{i}); fail{end+1} = names{i};
            end
        catch ME
            fprintf('[FAIL] %s : %s\n', names{i}, ME.message); fail{end+1} = names{i};
        end
    end
    fprintf('\n单元测试 %d/%d 通过\n', pass, numel(names));
    try
        r3 = run_assertions('Q3');
        fprintf('Q3 断言: %s\n', mat2str(r3));
    catch ME
        fprintf('Q3 断言异常: %s\n', ME.message);
    end
end
