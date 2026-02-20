#include <algorithm>
#include <cstdint>
#include <iostream>
#include <unordered_map>
#include <vector>

#include "edit_distance.h"

namespace docling {

constexpr int WORD_SIZE = sizeof(Word) * 8;
constexpr Word WORD_1 = static_cast<Word>(1);
constexpr Word HIGH_BIT = WORD_1 << (WORD_SIZE - 1);

EditDistanceCalculator::EditDistanceCalculator() {}

// Myers "Advance_Block": processes one block of one column.
// Pv/Mv encode the vertical deltas, Eq is the match vector for the current target token,
// hin is the horizontal delta entering from the block above.
// Returns hout (+1, 0, or -1) propagated to the next block.
int EditDistanceCalculator::calculate_block(Word Pv, // Element of Pv to read
                                            Word Mv, Word Eq, int hin, Word &PvOut, Word &MvOut) {
  Word hinIsNeg = static_cast<Word>(hin >> 2) & WORD_1;

  Word Xv = Eq | Mv;
  Eq |= hinIsNeg;
  Word Xh = (((Eq & Pv) + Pv) ^ Pv) | Eq;

  Word Ph = Mv | ~(Xh | Pv);
  Word Mh = Pv & Xh;

  int hout = 0;
  hout = (Ph & HIGH_BIT) >> (WORD_SIZE - 1);
  hout -= (Mh & HIGH_BIT) >> (WORD_SIZE - 1);

  Ph <<= 1;
  Mh <<= 1;
  Mh |= hinIsNeg;
  Ph |= static_cast<Word>((hin + 1) >> 1);

  PvOut = Mh | ~(Xv | Ph);
  MvOut = Ph & Xv;

  return hout;
}

int EditDistanceCalculator::edit_distance_raw(const std::vector<std::string> &query,
                                              const std::vector<std::string> &target) {
  // TODO: Do some vanity checks to ensure you will not run out of memory, have overflows, etc.

  const int n = static_cast<int>(query.size());
  const int m = static_cast<int>(target.size());

  if (n == 0) {
    return m;
  }
  if (m == 0) {
    return n;
  }

  // --- Map tokens to contiguous integer indices ---
  std::unordered_map<std::string, int> token_map;
  int next_id = 0;

  std::vector<int> q_idx(n); // vector with indices in the token_map
  for (int i = 0; i < n; i++) {
    auto [it, inserted] = token_map.try_emplace(query[i], next_id);
    if (inserted) {
      next_id++;
    }
    q_idx[i] = it->second;
  }

  std::vector<int> t_idx(m); // vector with indices in the token_map
  for (int i = 0; i < m; i++) {
    auto [it, inserted] = token_map.try_emplace(target[i], next_id);
    if (inserted) {
      next_id++;
    }
    t_idx[i] = it->second;
  }

  // TODO: Debug
  std::cout << "q_idx[0]=" << q_idx[0] << "\n";
  std::cout << "t_idx[0]=" << t_idx[0] << "\n";

  // --- Build Peq table ---
  // Peq[token_id][block] has bit i set iff query position (block*64 + i) matches token_id.
  // Tokens that only appear in the target get all-zero rows (no matches), which is the default.
  const int num_blocks = ceil_div(n, WORD_SIZE);
  const int W = num_blocks * WORD_SIZE - n; // padding bits in the last block

  // Check the memory footprint of the Peq
  // Initialize the dynamic matrix
  // Dimension: size-of-token_map x num-of-blocks
  // Initial value=0, uint64_t
  // Total size (bytes): size-of-token_map x num-of-blocks x 8
  std::cout << "n=" << n << ", m=" << m << "\n";
  std::cout << "num_blocks=" << num_blocks << "\n";
  std::cout << "WORD_SIZE=" << WORD_SIZE << "\n";
  std::cout << "W=" << W << "\n";
  std::cout << "token_map.size()=" << token_map.size() << ", next_id=" << next_id << "\n";

  std::vector<std::vector<Word>> Peq(next_id, std::vector<Word>(num_blocks, 0));
  for (int i = 0; i < n; i++) {
    Peq[q_idx[i]][i / WORD_SIZE] |= WORD_1 << (i % WORD_SIZE);
  }

  // --- Initialise block state ---
  std::vector<Word> Pv(num_blocks, ~Word(0)); // all 1s
  std::vector<Word> Mv(num_blocks, 0);
  std::vector<int> scores(num_blocks);
  for (int b = 0; b < num_blocks; b++) {
    scores[b] = (b + 1) * WORD_SIZE; // TODO: How do we know there is no overflow?
  }

  // --- Process each target token ---
  for (int j = 0; j < m; j++) {
    const std::vector<Word> &eq = Peq[t_idx[j]]; // The Peq vector corresponding to the target token
    int hin = 1;                                 // NW: gap before query is penalised

    for (int b = 0; b < num_blocks; b++) {
      hin = calculate_block(Pv[b], Mv[b], eq[b], hin, Pv[b], Mv[b]);
      scores[b] += hin;
    }
  }

  // --- Extract score at the real last query position ---
  // The last block may contain W padding cells at the high-bit end.
  // Walk back from the bottommost cell to undo the padding.
  int score = scores[num_blocks - 1];
  Word mask = HIGH_BIT;
  for (int i = 0; i < W; i++) {
    if (Pv[num_blocks - 1] & mask) {
      score--;
    }
    if (Mv[num_blocks - 1] & mask) {
      score++;
    }
    mask >>= 1;
  }

  return score;
}

double EditDistanceCalculator::edit_distance(const std::vector<std::string> &query,
                                             const std::vector<std::string> &target) {
  const int max_len = std::max(static_cast<int>(query.size()), static_cast<int>(target.size()));
  if (max_len == 0) {
    return 0.0;
  }
  return static_cast<double>(edit_distance_raw(query, target)) / max_len;
}

} // namespace docling
