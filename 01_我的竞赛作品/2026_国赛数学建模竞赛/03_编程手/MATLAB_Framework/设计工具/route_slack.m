function route_slack()
% route_slack —— 真机局的"路由松弛"实测：实走 vs 同一批点的 2-opt+Or-opt 巡游
% 若两者接近 ⇒ 路由已到顶，别再投入；若差得多 ⇒ 值得重构阶段 A 的调度。
    root = fullfile(fileparts(fileparts(mfilename('fullpath'))), 'logs');
    files = {'robot_202623005040_20260913_135120.jsonl', ...
             'robot_202623005040_20260913_135206.jsonl', ...
             'robot_202623005040_20260913_135235.jsonl', ...
             'robot_202623005040_20260913_135434.jsonl'};
    fprintf('\n%-14s %10s %10s %8s %6s\n', 'log', '实走(m)', '重排(m)', '比值', '点数');
    fprintf('%s\n', repmat('-', 1, 56));
    for i = 1:numel(files)
        recs = read_jsonl(fullfile(root, files{i}));
        P = zeros(0, 2);
        for k = 1:numel(recs)
            r = recs{k};
            if ~isfield(r, 'kind') || ~strcmp(r.kind, 'request'), continue; end
            if ~isfield(r, 'accepted') || ~r.accepted, continue; end
            rp = r.request_payload;
            if ~isstruct(rp) || ~isfield(rp, 'position'), continue; end
            P(end+1, :) = [rp.position.x, rp.position.y]; %#ok<AGROW>
        end
        if size(P, 1) < 3, continue; end
        travel = sum(vecnorm(diff(P), 2, 2));
        sp = P(1, :);
        % 同一批点（含重复），从同一落点出发，用生产同款优化器重排
        route = optimize_route(P, sp);
        re = 0; prev = sp;
        for k = route(:)'
            re = re + norm(P(k, :) - prev); prev = P(k, :);
        end
        fprintf('%-14s %10.0f %10.0f %8.3f %6d\n', files{i}(20:25), travel, re, re/travel, size(P,1));
    end
end

function recs = read_jsonl(p)
    recs = {}; 
    if ~exist(p, 'file'), return; end
    fid = fopen(p, 'r', 'n', 'UTF-8');
    if fid <= 0, return; end
    while ~feof(fid)
        l = fgetl(fid);
        if ~ischar(l) || isempty(strtrim(l)), continue; end
        try, recs{end+1} = jsondecode(l); catch, end %#ok<AGROW>
    end
    fclose(fid);
end
