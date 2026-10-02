#include <algorithm>
#include <cstdint>
#include <queue>
#include <utility>
#include <vector>

// No geometry assertion is trusted: the Python receiver recomputes the packet.
// Validate CSR and ordering before indexing memory. Return -1 on invalid input,
// -2 on incomplete cover; otherwise return number of chosen rows.
extern "C" int64_t cover_select(int64_t n, int64_t cells, int64_t edges,
                                const int64_t* ptr, const int64_t* col,
                                const int64_t* order, int mode, int64_t* output) {
    if (n < 0 || n > 500000 || cells < 0 || cells > 2000000 ||
        edges < 0 || edges > 20000000 || (mode != 0 && mode != 1) ||
        ptr[0] != 0 || ptr[n] != edges) return -1;
    std::vector<int64_t> counts(cells, 0);
    std::vector<unsigned char> seen(n, 0);
    for (int64_t i = 0; i < n; ++i) {
        if (ptr[i] < 0 || ptr[i+1] < ptr[i] || ptr[i+1] > edges) return -1;
        for (int64_t j = ptr[i]; j < ptr[i+1]; ++j) {
            if (col[j] < 0 || col[j] >= cells ||
                (j > ptr[i] && col[j] <= col[j-1])) return -1;
            ++counts[col[j]];
        }
        if (order[i] < 0 || order[i] >= n || seen[order[i]]) return -1;
        seen[order[i]] = 1;
    }
    for (auto count : counts) if (!count) return -2;
    if (mode == 0) { // The exact reverse deletion order from the reference.
        std::vector<unsigned char> keep(n, 1);
        for (int64_t k = 0; k < n; ++k) {
            int64_t i = order[k];
            bool redundant = true;
            for (int64_t j = ptr[i]; j < ptr[i+1]; ++j)
                if (counts[col[j]] < 2) { redundant = false; break; }
            if (redundant) {
                keep[i] = 0;
                for (int64_t j = ptr[i]; j < ptr[i+1]; ++j) --counts[col[j]];
            }
        }
        int64_t used = 0;
        for (int64_t i = 0; i < n; ++i) if (keep[i]) output[used++] = i;
        return used;
    }
    // Exact largest-current-gain greedy. Heap entries are upper bounds until
    // checked; a current entry at the top is the global maximum. Ties select
    // the smallest original row index, as in the established Python baseline.
    std::priority_queue<std::pair<int64_t, int64_t>> heap;
    for (int64_t i = 0; i < n; ++i)
        if (ptr[i+1] > ptr[i]) heap.push({ptr[i+1]-ptr[i], -i});
    std::vector<unsigned char> missing(cells, 1);
    int64_t remaining = cells, used = 0;
    while (remaining) {
        if (heap.empty()) return -2;
        auto top = heap.top(); heap.pop();
        int64_t i = -top.second, gain = 0;
        for (int64_t j = ptr[i]; j < ptr[i+1]; ++j) gain += missing[col[j]];
        if (gain != top.first) {
            if (gain) heap.push({gain, -i});
            continue;
        }
        if (!gain) return -2;
        output[used++] = i;
        for (int64_t j = ptr[i]; j < ptr[i+1]; ++j) {
            if (missing[col[j]]) { missing[col[j]] = 0; --remaining; }
        }
    }
    return used;
}
