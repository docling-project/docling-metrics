#pragma once
#include <iostream>
#include <string>
#include <memory>
#include <algorithm>

#include "node.h"
#include "string_label.h"
#include "unit_cost_model.h"
#include "bracket_notation_parser.h"
#include "apted_tree_index.h"


namespace docling {

using Label = label::StringLabel;
using CostModelLD = cost_model::UnitCostModelLD<Label>;
using LabelDictionary = label::LabelDictionary<Label>;


class TEDSManager {
public:
    TEDSManager();

    /**
     * Evaluate a single sample
     */
    double eval_sample(const std::string& gt_bracket, const std::string& pred_bracket);

    // void aggregate();
    //
    // void eval_dataset();

private:
    parser::BracketNotationParser<Label> bnp_;
    LabelDictionary ld_;
    std::unique_ptr<CostModelLD> ucm_ptr_ = nullptr;
    std::unique_ptr<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>> apted_ptr_;
};


////////////////////////////////////////////////////////////////////////////////////////////
// Implementation
//

TEDSManager::TEDSManager():
    ucm_ptr_(std::make_unique<CostModelLD>(ld_)),
    apted_ptr_(std::make_unique<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>>(*ucm_ptr_))
{
    std::cout << "Initializing TEDSManager\n";
}

double TEDSManager::eval_sample(const std::string& gt_bracket, const std::string& pred_bracket) {
    /*
     * TODO:
     * - Throw exception of our type in case of invalid input
     * - Return object with full information: teds, tree sizes, ...
     */

    // Create gt_tree
    if (!bnp_.validate_input(gt_bracket)) {
        std::cerr << "Incorrect format of source tree. Is the number of opening and closing brackets equal?" << std::endl;
        return -1.;
    }
    const node::Node<Label> gt_tree = bnp_.parse_single(gt_bracket);

    // Create pred_tree
    if (!bnp_.validate_input(pred_bracket)) {
        std::cerr << "Incorrect format of destination tree. Is the number of opening and closing brackets equal?" << std::endl;
        return -1.;
    }
    const node::Node<Label> pred_tree = bnp_.parse_single(pred_bracket);


    // Compute ted
    int gt_tree_size = gt_tree.get_tree_size();
    int pred_tree_size = pred_tree.get_tree_size();
    int max_tree_size = std::max(gt_tree_size, pred_tree_size);

    node::TreeIndexAPTED ti1;
    node::TreeIndexAPTED ti2;
    node::index_tree(ti1, gt_tree, ld_, *ucm_ptr_);
    node::index_tree(ti2, pred_tree, ld_, *ucm_ptr_);
    double distance = apted_ptr_->ted(ti1, ti2);
    double teds = 1. - (distance / max_tree_size);

    return teds;
}

} // namespace docling

