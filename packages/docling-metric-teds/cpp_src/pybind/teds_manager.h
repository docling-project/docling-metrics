#pragma once
#include <iostream>
#include <string>
#include <memory>
#include <algorithm>
#include <unordered_map>

#include "node.h"
#include "string_label.h"
#include "unit_cost_model.h"
#include "bracket_notation_parser.h"
#include "apted_tree_index.h"


namespace docling {

using Label = label::StringLabel;
using CostModelLD = cost_model::UnitCostModelLD<Label>;
using LabelDictionary = label::LabelDictionary<Label>;


struct TEDSSampleEvaluation {
    TEDSSampleEvaluation(): TEDSSampleEvaluation("") {}

    TEDSSampleEvaluation(const std::string& sid):
        error_id(0), error_msg(""), id(sid), gt_tree_size(0), pred_tree_size(0), teds(-1.)
    {}

    int error_id;
    std::string error_msg;
    std::string id;
    int gt_tree_size;
    int pred_tree_size;
    double teds;
};


struct TEDSDatasetEvaluation {
    TEDSDatasetEvaluation(): TEDSDatasetEvaluation("") {}

    TEDSDatasetEvaluation(const std::string& sid):
        error_id(0), error_msg(""), teds(-1.)
    {}

    int error_id;
    std::string error_msg;
    double teds;
    std::unordered_map<std::string, TEDSSampleEvaluation> sample_evaluations;
};


class TEDSManager {
public:
    TEDSManager():
        ucm_ptr_(std::make_unique<CostModelLD>(ld_)),
        apted_ptr_(std::make_unique<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>>(*ucm_ptr_))
    { }
    
    /**
     * Evaluate a single sample in html format
     */
    TEDSSampleEvaluation evaluate_html_sample(
        const std::string& id,
        const std::string& html_a,
        const std::string& html_b,
        bool structure_only
    ) {
        // Convert the html to bracket format
        std::string bracket_a = html_to_bracket(html_a, structure_only);
        std::string bracket_b = html_to_bracket(html_b, structure_only);

        return evaluate_sample(
            id,
            bracket_a,
            bracket_b
        );
    }

    /**
     * Evaluate a single sample
     */
    TEDSSampleEvaluation evaluate_sample(
        const std::string& id,
        const std::string& bracket_a,
        const std::string& bracket_b
    ) {
        // Return object with full information: teds, tree sizes, ...
        TEDSSampleEvaluation eval_sample(id);

        // Create gt_tree
        if (!bnp_.validate_input(bracket_a)) {
            eval_sample.error_id = 1;
            eval_sample.error_msg = "Incorrect format of the ground truth input";
            return eval_sample;
        }
        const node::Node<Label> gt_tree = bnp_.parse_single(bracket_a);

        // Create pred_tree
        if (!bnp_.validate_input(bracket_b)) {
            eval_sample.error_id = 2;
            eval_sample.error_msg = "Incorrect format of the predictions input";
            return eval_sample;
        }
        const node::Node<Label> pred_tree = bnp_.parse_single(bracket_b);

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

        eval_sample.gt_tree_size = gt_tree_size;
        eval_sample.pred_tree_size = pred_tree_size;
        eval_sample.teds = teds;

        return eval_sample;
    }

    void aggregate() {}

    TEDSDatasetEvaluation evaluate_dataset() {
        // TODO: Add implementation
        TEDSDatasetEvaluation eval_dataset;
        return eval_dataset;
    }

private:
    std::string html_to_bracket(const std::string& html, bool structure_only) {
        // TODO: Add implementation
        return "";
    }

private:
    parser::BracketNotationParser<Label> bnp_;
    LabelDictionary ld_;
    std::unique_ptr<CostModelLD> ucm_ptr_ = nullptr;
    std::unique_ptr<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>> apted_ptr_;

    // Accumulated evaluations per sample
    std::unordered_map<std::string, TEDSSampleEvaluation> sample_evaluations;
};

} // namespace docling

