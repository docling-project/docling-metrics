#pragma once

#include <string>
#include <vector>

namespace docling {

// Myers bit-vector edit distance on token sequences (Needleman-Wunsch / global).
// Returns the raw edit distance (number of insertions, deletions, substitutions).
int edit_distance_raw(const std::vector<std::string> &query,
                      const std::vector<std::string> &target);

// Normalized edit distance: raw distance divided by max(|query|, |target|).
// Returns 0.0 when both sequences are empty.
double edit_distance(const std::vector<std::string> &query, const std::vector<std::string> &target);

} // namespace docling
