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

    // TODO: How to have teds with/without content
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
        const std::string& gt_html,
        const std::string& pred_html
    ) {
        return evaluate_sample(
            id,
            html_to_bracket(gt_html),
            html_to_bracket(pred_html)
        );
    }

    /**
     * Evaluate a single sample
     */
    TEDSSampleEvaluation evaluate_sample(
        const std::string& id,
        const std::string& gt_bracket,
        const std::string& pred_bracket
    ) {
        // Return object with full information: teds, tree sizes, ...
        TEDSSampleEvaluation eval_sample(id);

        // Create gt_tree
        if (!bnp_.validate_input(gt_bracket)) {
            eval_sample.error_id = 1;
            eval_sample.error_msg = "Incorrect format of the ground truth input";
            return eval_sample;
        }
        const node::Node<Label> gt_tree = bnp_.parse_single(gt_bracket);

        // Create pred_tree
        if (!bnp_.validate_input(pred_bracket)) {
            eval_sample.error_id = 2;
            eval_sample.error_msg = "Incorrect format of the predictions input";
            return eval_sample;
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
    std::string html_to_bracket(const std::string& html) {
        // TODO
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

