# train_args.py
import argparse
import math

def parse_args():

    parser = argparse.ArgumentParser()

    # argparse groups
    model_group = parser.add_argument_group('model_group')
    training_group = parser.add_argument_group('training_group')
    logging_group = parser.add_argument_group('logging_group')

    # Export Args
    ## Factored WTE
    model_group.add_argument('--import_wte_npy', default=None, type=str, help='Path to import the embedding table as a .npy file')
    model_group.add_argument('--export_wte_npy', default=None, type=str, help='Path to export the embedding table as a .npy file')
    model_group.add_argument('--export_wte_each_eval', default=False, action=argparse.BooleanOptionalAction, help="Requires --export_wte is not None. If this is so, will always export embedding to numpy after evaluation")
    model_group.add_argument('--import_wte_freeze', default=False, action=argparse.BooleanOptionalAction, help="Whether to freeze an imported wte")

    ## Factored Scale Matrices
    model_group.add_argument('--import_scale_matrices_npz', default=None, type=str, help='Path to import the scale matrices as a .npz file')
    model_group.add_argument('--export_scale_matrices_npz', default=None, type=str, help='Path to export the scale matrices as a .npz file')
    model_group.add_argument('--export_scale_matrices_each_eval', default=False, action=argparse.BooleanOptionalAction, help="Requires --export_scale_matrices_npz is not None. If this is so, will always export to npz after evaluation")
    model_group.add_argument('--import_scale_matrices_freeze', default=False, action=argparse.BooleanOptionalAction, help="Whether to freeze scaled_matrices")

    # I/O args
    training_group.add_argument('--out_dir', default='out', type=str)
    training_group.add_argument('--eval_interval', default=250, type=int)
    training_group.add_argument('--log_interval', default=10, type=int)
    training_group.add_argument('--eval_iters', default=200, type=int)
    training_group.add_argument('--eval_only', default=False, action=argparse.BooleanOptionalAction)

    # Loss variations
    training_group.add_argument('--focus_on_top1_loss', default=False, action=argparse.BooleanOptionalAction)

    # Sample args
    training_group.add_argument('--max_sample_tokens', default=None, type=int, help="If set, maximum number of tokens to sample and print after each validation loss")
    training_group.add_argument('--sample_each_eval', default=False, action=argparse.BooleanOptionalAction, help="Produce sample even if the validation loss did not improve. Allows for testing what overtraining looks like.")
    training_group.add_argument('--sample_start_tokens', default='\n', type=str)
    training_group.add_argument('--sample_only', default=False, action=argparse.BooleanOptionalAction, help="Run only the sampling process and exit")

    # Checkpoint args
    training_group.add_argument('--save_major_ckpt_interval', default=None, type=int, help="Interval for saving major checkpoints.")
    training_group.add_argument('--only_save_checkpoint_at_end', default=False, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--always_save_checkpoint', default=False, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--patience', default=None, type=int, help="if set, will stop training if the number of evaluations since val loss was seen to decrease exceeds 'patience' setting.")
    training_group.add_argument('--init_from', default='scratch', choices=['scratch', 'prev_run', 'resume', 'gpt2'], type=str)
    training_group.add_argument('--gpt2_type', default='gpt2', type=str)
    training_group.add_argument('--prev_run_ckpt', default='', type=str)
    training_group.add_argument('--csv_ckpt_dir', default='', type=str)
    training_group.add_argument('--init_from_ckpt', default='ckpt.pt', type=str, help="if save_major_ckpt_interval was set, can use to init from specific ckpts")

    # Data args
    training_group.add_argument('--dataset', default='shakespeare_char', type=str)
    training_group.add_argument('--batch_size', default=64, type=int)
    training_group.add_argument("--seed", default=1337, type=int)

    # New: total tokens in dataset (for computing epochs) and sampling method
    training_group.add_argument('--dataset_size_tokens', default=None, type=int,
        help="Total number of tokens in the dataset (used for reporting epoch progress)")
    training_group.add_argument('--sampling_method', default="random",
        choices=["random", "sequential", "without_replacement"],
        help="Sampling method for get_batch: 'random' (with replacement), 'sequential' (without shuffling), or 'without_replacement' (shuffled without replacement)")

    # Add a new argument for specifying multiple datasets
    training_group.add_argument('--dataset_list', default=None, nargs='+', type=str, help="If not None, training will be done from a list of datasets to train on, e.g. --dataset_list shakespeare wikitext103 openwebtext")
    training_group.add_argument('--dataset_interleaving', default=False, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--dataset_interleaving_shuffle', default=False, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--dataset_sampling_learning_rate', default=None, nargs='+', type=float, help="Sampling learning rates for each dataset in dataset_list.")
    training_group.add_argument('--dataset_sampling_probs', action=FlattenListAction, default=None, nargs='+', help="Sampling proportions for each dataset in dataset_list. Probabilities normally but proportions in dataset_interleaving")
    training_group.add_argument('--dataset_sampling_probs_final', action=FlattenListAction,default=None, nargs='+', help="If, set final sampling probabilities for each dataset in dataset_list.")
    training_group.add_argument('--dataset_sampling_probs_transition_method', default=None, type=str, choices=["linear", "cosine", "exponential"])

    # Add GNS settings
    training_group.add_argument('--gns_type', type=str, default=None, choices=['sogns', 'exact'], help='Type of gradient norm scaling to use (default: None)')
    training_group.add_argument('--gns_ema_beta', type=float, default=0.9, choices=['sogns', 'exact'], help='Type of gradient norm scaling to use (default: None)')
    training_group.add_argument('--gns_target', type=float, default=None)
    training_group.add_argument('--gns_max_batch', type=int, default=100)
    training_group.add_argument('--gns_batch_pct', type=float, default=0.2)


    # Optimizer-specific arguments
    optimizer_variations = ["adamw",
                            "sgd",
                            "adagrad",
                            "rmsprop",
                            "nadam",
                            ]
    training_group.add_argument("--optimizer", type=str, default="adamw",
                                 choices=optimizer_variations,
                                 help="Optimizer to use for training.")

    training_group.add_argument("--sgd_momentum", type=float, default=0.9, help="Momentum for SGD optimizer.")
    training_group.add_argument("--adamw_betas", type=float, nargs=2, default=[0.9, 0.999], help="Betas for AdamW optimizer.")
    training_group.add_argument("--adamw_eps", type=float, default=1e-8, help="Epsilon for AdamW optimizer.")
    training_group.add_argument("--adamw_weight_decay", type=float, default=0.01, help="Weight decay for AdamW optimizer.")
    training_group.add_argument("--adagrad_lr_decay", type=float, default=0, help="Learning rate decay for Adagrad optimizer.")
    training_group.add_argument("--rmsprop_alpha", type=float, default=0.99, help="Smoothing constant for RMSprop.")
    training_group.add_argument("--nadam_betas", type=float, nargs=2, default=[0.9, 0.999], help="Betas for Nadam optimizer.")
    training_group.add_argument("--nadam_eps", type=float, default=1e-8, help="Epsilon for Nadam optimizer.")


    # Learning rate scheduler-specific arguments
    scheduler_variations = ["none",
                            "cosine",
                            "exponential",
                            "step",
                            "plateau",
                            ]
    training_group.add_argument("--lr_scheduler", type=str, default="none",
                                choices= scheduler_variations,
                                help="Learning rate scheduler to use.")

    training_group.add_argument("--cosine_t_max", type=int, default=1000, help="T_max parameter for CosineAnnealingLR.")
    training_group.add_argument("--cosine_eta_min", type=float, default=0, help="Minimum learning rate for CosineAnnealingLR.")
    training_group.add_argument("--exponential_gamma", type=float, default=0.9, help="Gamma value for ExponentialLR.")
    training_group.add_argument("--step_lr_size", type=int, default=1000, help="Step size for StepLR.")
    training_group.add_argument("--step_lr_gamma", type=float, default=0.1, help="Gamma value for StepLR.")
    training_group.add_argument("--plateau_mode", type=str, default="min", choices=["min", "max"], help="Mode for ReduceLROnPlateau.")
    training_group.add_argument("--plateau_factor", type=float, default=0.1, help="Factor by which learning rate is reduced for ReduceLROnPlateau.")
    training_group.add_argument("--plateau_patience", type=int, default=10, help="Number of epochs with no improvement for ReduceLROnPlateau.")


    # Training sample *args
    training_group.add_argument('--interactive', default=False, action=argparse.BooleanOptionalAction, help="Enable interactive generation at the end of training (similar to sample.py --interactive).")
    training_group.add_argument('--stop_string', type=str, default='~W', help="String to stop generation and allow user input (used when --interactive).")
    training_group.add_argument('--colorize_output', default=True, action=argparse.BooleanOptionalAction, help="Colorize tokens based on predicted probabilities.")
    training_group.add_argument('--colorize_mode', type=str, default='minmax', choices=['minmax', 'softmax', 'softmax_top_k'], help="Colorization mode for tokens (see sample.py).")
    training_group.add_argument('--show_heatmaps', default=False, action=argparse.BooleanOptionalAction, help="Show heatmaps (or bar charts) of top-k token probabilities.")
    training_group.add_argument('--chart_type', type=str, default='heatmap', choices=['heatmap', 'barchart'], help="Type of chart to display if --show_heatmaps is set.")
    training_group.add_argument('--last_k_tokens', type=int, default=10, help="Number of last tokens to display in heatmaps or bar charts.")
    training_group.add_argument('--sample_file', type=str, default=None, help="Output file for inference samples (if you want to save them).")
    training_group.add_argument('--token_boundary', type=str, default=None, help="Optional separator string between emitted tokens (for decode).")
    training_group.add_argument('--num_samples', type=int, default=1, help="Number of generated samples during sampling.")
    training_group.add_argument('--temperature', type=float, default=0.8, help="Temperature for predictions (1.0 = normal, < 1.0 = less random).")
    training_group.add_argument('--top_k', type=int, default=200, help="Retain only the top_k most likely tokens (used in sample.py).")
    training_group.add_argument('--eval_dataset', type=str, default=None, help="Optional dataset name for custom evaluation splits.")
    training_group.add_argument('--quantization_data_file', type=str, default=None, help="If set, export quantized weights/activations to a specified file (pkl).")

    # Model args
    model_group.add_argument('--block_size', default=256, type=int)
    model_group.add_argument('--n_layer', default=6, type=int)
    model_group.add_argument('--n_head', default=6, type=int)
    model_group.add_argument('--n_kv_group', default=None, type=int)
    model_group.add_argument('--n_embd', default=384, type=int, help="Size of embeddings in decoder layer and wte unless n_embd_wte is set." )
    model_group.add_argument('--n_embd_wte', default=None, type=int, help="If different from n_embd, an adapter table will be automatically created")
    model_group.add_argument('--n_embd_wte_scale_tying', default=True, action=argparse.BooleanOptionalAction, help="Enable weight tying for scale up and scale down matrices, only has effects if n_embd_wte is not 'None'.")
    model_group.add_argument('--dropout', default=0.2, type=float)
    model_group.add_argument('--use_post_ln', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--window_size', default=None, type=int, help="Sliding window size, note this cannot be greater than block size")
    model_group.add_argument('--gate', default=False, action=argparse.BooleanOptionalAction, help="option for gated attention see https://arxiv.org/abs/2306.12929")
    model_group.add_argument('--use_moe', default=False,  action=argparse.BooleanOptionalAction, help="option for Mixture of Experts (MoE) architecture")
    model_group.add_argument('--moe_layer_freq', default=2, type=int, help="set frequency for replacing FFNs with MoE layers")
    model_group.add_argument('--n_experts', default=8, type=int, help="set number of experts per MoE layer")
    model_group.add_argument('--moe_top_k', default=2, type=int)
    model_group.add_argument('--moe_router_scheme', default="softmax", type=str, help="option to set routing scheme for MoE layer, defaults to softmax")
    model_group.add_argument('--use_flex_attn', default=None,  action=argparse.BooleanOptionalAction, help="option for using flex attention for sliding windows")


    ## Manual Steering Vector Options

    ### Applying Steering Vectors
    model_group.add_argument('--apply_vector_at_layer_idx', default=None, type=int)
    model_group.add_argument("--apply_vector_file", type=str, default=None, help="single vector to apply with scaling factor")
    model_group.add_argument("--apply_vector_scaling_factor", type=float, default=1.0, help="scaling factor to apply to steering vector")

    ### Options for intercepting and obtaining vectors
    model_group.add_argument('--obtain_vector_at_layer_idx', default=None, type=int)
    model_group.add_argument("--obtain_vector_file", type=str, default=None, help="initial KAN activation")

    ## Learned Steering Vector (LSV) Options
    lsv_variations = [
            "one_hot",
            "linear_comb",
            "one_hot_mlp",
            "ohmg",
            "ohmt",
            "ohmm",
            "ohma",
            "ohmgu",
            "ohmh",
            "mol",
        ]
    model_group.add_argument("--use_lsv", default=False, action=argparse.BooleanOptionalAction, help="whether to use Learned Steering Vectors")
    model_group.add_argument("--lsv_index", default=None, type=int, help="Which steering vector to use")
    model_group.add_argument("--lsv_variant", default="one_hot", type=str, choices=lsv_variations, help="Which steering vector to use")
    model_group.add_argument('--apply_lsv_at_layer_idx', default=None, type=int)

    training_group.add_argument("--lsv_focused_training", default=False, action=argparse.BooleanOptionalAction, help="train but only unfreeze lsv")

    ## MLP Options
    model_group.add_argument('--use_parallel_mlp', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--mlp_variant", type=str, default="mlp", choices=["mlp", "kan", "swiglu"], help="MLP variation type")
    model_group.add_argument("--mlp_expansion_factor", type=int, default=4, help="If MLP like variant is used, set the expansion factor for the linear transformations, default is 4.")

    ## KAN Options
    model_group.add_argument("--kan_poly_order", type=int, default=3, help="Order of KAN non-linearity")
    model_group.add_argument("--kan_base_activation", type=str, default="silu", help="initial KAN activation")
    model_group.add_argument("--kan_middle_layers", type=int, nargs='+', help="List of integers", default=[])

    # Shared Parameter Settings
    model_group.add_argument('--shared_mlp_size', default=1, type=int, help="every 'k' contiguous blocks of mlp are shared")
    model_group.add_argument('--shared_mlp_sym', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--shared_attn_size', default=1, type=int, help="every 'k' contiguous blocks of attn are shared")
    model_group.add_argument('--shared_attn_sym', default=False, action=argparse.BooleanOptionalAction, help="symmetrical attention sharing")

    # NORM VARIATIONS
    norm_variations = [
            "krmsnorm",
            "prmsnorm",
            "rmsnorm",
            "layernorm",
            "hyperspherenorm",
            "dact",
            ]

    model_group.add_argument("--norm_variant_attn", type=str, default="rmsnorm", choices=norm_variations)
    model_group.add_argument("--norm_variant_output", type=str, default="rmsnorm", choices=norm_variations)

    ## Layernorm
    model_group.add_argument('--bias', default=False, action=argparse.BooleanOptionalAction, help="only used for layernorm variation option")

    ## PRMSNorm
    model_group.add_argument("--prmsnorm_pct", default=0.0625, type=float, help="percentage (1 being 100 percent) of first entries used for partial rms" )

    ## KRMSNorm
    model_group.add_argument("--krmsnorm_num", default=10, type=int, help="max number of first entries for partial rms" )
    model_group.add_argument("--krmsnorm_quantize_type", type=str, default="none", choices=["int8", "int16", "none"])
    model_group.add_argument('--krmsnorm_enable_gain', default=True, action=argparse.BooleanOptionalAction, help="include gain in kRMSNorm")
    model_group.add_argument("--krmsnorm_selection_type", type=str, default="last", choices=["first", "last", "random"])
    model_group.add_argument("--krmsnorm_recompute_percentage", type=float, default=None, help="percentage needed within the total RMS to not trigger recompute")

    ## HyperSphereNorm
    model_group.add_argument("--hsnorm_gain", default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--hsnorm_radius", type=float, default=None)
    model_group.add_argument("--hsnorm_radius_learning", default=False, action=argparse.BooleanOptionalAction)

    activation_variations = [
            "celu",
            "elu",
            "gelu",
            "gelu_shifted",
            "glu",
            "leaky_relu",
            "learned_spline",
            "mish",
            "piecewise",
            "pfla",
            "pfla_le",
            "prelu",
            "relu",
            "relu6",
            "rrelu",
            "selu",
            "sigmoid",
            "silu",
            "softplus",
            "softsign",
            "squared_relu",
            "tanh",
        ]

    ## DynamicActivations
    model_group.add_argument("--dact_alpha_init", default=1.0, type=float)
    model_group.add_argument("--dact_activation", type=str, default="tanh", choices=activation_variations)

    # ACTIVATION VARIATIONS
    model_group.add_argument( "--activation_variant", type=str, default="gelu", choices=activation_variations)

    ## Shifted Gelu
    model_group.add_argument("--shifted_gelu_learnable_shift",  type=bool, default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--shifted_gelu_initial_shift", type=float, default=0.0)

    ## PiecewiseLearnableActivation - pla
    model_group.add_argument("--pla_num_points", type=int, default=7)
    model_group.add_argument("--pla_left_bound", type=float, default=-2.0)
    model_group.add_argument("--pla_right_bound", type=float, default=2.0)

    ## PiecewiseFullyLearnableActivation - pfla
    model_group.add_argument("--pfla_num_points", type=int, default=200)
    model_group.add_argument("--pfla_left_bound", type=float, default=-100.0)
    model_group.add_argument("--pfla_right_bound", type=float, default=100.0)

    ## PiecewiseFullyLearnableActivationLearnedEnds - pflale
    model_group.add_argument("--pfla_le_num_points",   type=int,  default=30)
    model_group.add_argument("--pfla_le_left_bound",  type=float, default=-10.0)
    model_group.add_argument("--pfla_le_right_bound", type=float, default=10.0)

    ## LearnedSplineActivation - lsa
    model_group.add_argument("--lsa_num_knots", type=int, default=30)


    # Attention Variations
    attention_variants = ["causal", "linear", "ssm", "identity", "infinite"]

    model_group.add_argument(
        "--attention_list",
        nargs='+',
        type=str,
        default=None,
        help="List of attention variants to cycle through, e.g. 'causal linear ssm'."
    )

    model_group.add_argument(
        "--attention_variant",
        type=str,
        default="causal",
        choices=attention_variants,
        help="Which attention variant to use for the Transformer blocks."
    )

    # Inifinite Attention variation
    model_group.add_argument('--n_head_dim', default=None, type=int)

    ## SSM - Attention Varient (same as Hymba)
    model_group.add_argument("--ssm_mamba_expand",   type=int,  default=2)
    model_group.add_argument("--ssm_conv_kernel_size",   type=int,  default=3)
    model_group.add_argument("--ssm_dt_rank",   type=int,  default=8)
    model_group.add_argument("--ssm_d_state",   type=int,  default=16)
    model_group.add_argument("--ssm_io_bias",   type=bool, default=False, action=argparse.BooleanOptionalAction, help="adds biases for nn.linear() of both in_proj and out_proj")

    # LINEAR VARIATIONS
    linear_variants = ["linear", "bitlinear", "bitlinear_1p58", "bitlinear_optimized", "kan","quantized_linear"]
    model_group.add_argument("--linear_variant_attn", type=str, default="linear", choices=linear_variants)
    model_group.add_argument("--linear_variant_q", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_attn_q in attention (takes precedence over linear_variant_attn)")
    model_group.add_argument("--linear_variant_k", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_attn_k in attention (takes precedence over linear_variant_attn)")
    model_group.add_argument("--linear_variant_v", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_attn_v in attention (takes precedence over linear_variant_attn)")
    model_group.add_argument("--linear_variant_attn_proj", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_proj in attention (takes precedence over linear_variant_attn)")
    model_group.add_argument("--linear_variant_mlp", type=str, default="linear", choices=linear_variants)
    model_group.add_argument("--linear_variant_mlp_up", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_fc in mlp (takes precedence over linear_variant_mlp)")
    model_group.add_argument("--linear_variant_mlp_down", type=str, default=None, choices=linear_variants, help="sets the linear variant for c_proj in mlp (takes precedence over linear_variant_mlp)")
    ## Linear Weight Initialization Options
    model_group.add_argument( "--linear_mean_init", type=float, default=0.0)
    model_group.add_argument( "--linear_std_init", type=float, default=0.02)

    ## Embedding Weight Initialization Options
    embedding_init_variations = ["gaussian", "onehot", "hypercube"]
    model_group.add_argument( "--init_variant", choices=embedding_init_variations, default="gaussian", help="options for embedding initializations")

    # Quantization
    model_group.add_argument("--full_quant_iteration", type=int, default=None,
                             help="The iteration where the model reaches full quantization. The increase from start_quant_level to full quantization is determined by the quant_scheduler.")
    model_group.add_argument("--start_quant_level", type=float, default=0.0,
                             help="Starting level of quantization. A quant level of 0 means that there is no quantization is occurring. A quant level of 1 is full quantization.")
    model_group.add_argument("--quant_scheduler", type=str, default=None, choices=["static", "linear"],
                             help="Scheduler for change in quant level. When linear is set, the quantization will increase dynamically based on the training step")

    ## Quantization Method Options
    quant_methods = ["ternary_quant", "symmetric_quant", "affine_quant", "stochastic_quant"]

    ## WTE
    model_group.add_argument("--quantize_wte", default=None, action=argparse.BooleanOptionalAction, help="Whether the word embedding is quantized")
    model_group.add_argument("--quantize_wte_method", type=str, default="affine_quant", choices=quant_methods, help="function used for word embedding quantization")
    model_group.add_argument("--quantize_wte_bits", type=int, default=8, help="number of bits for word embedding quantization")

    ## WPE
    model_group.add_argument("--quantize_wpe", default=None, action=argparse.BooleanOptionalAction, help="Whether the word position embedding is quantized")
    model_group.add_argument("--quantize_wpe_method", type=str, default="affine_quant", choices=quant_methods, help="function used for position embedding quantization")
    model_group.add_argument("--quantize_wpe_bits", type=int, default=8, help="number of bits for position embedding quantization")

    ## Activations
    model_group.add_argument("--activations_quant_method", type=str, default="affine_quant", choices=quant_methods, help="function used for quantization of activations")

    ### Attention Activations
    model_group.add_argument("--quantize_attn_act", action=argparse.BooleanOptionalAction, default=False, help="quantize all input/output activations in attn")

    #### Whether to do Attention Activation quantization at the Arrow
    model_group.add_argument("--quantize_attn_act_input", action=argparse.BooleanOptionalAction, default=False, help="quantize input activation to attention")
    model_group.add_argument("--quantize_attn_act_qk_mult_q_input", action=argparse.BooleanOptionalAction, default=False, help="quantize query input activation to qk mult")
    model_group.add_argument("--quantize_attn_act_qk_mult_k_input", action=argparse.BooleanOptionalAction, default=False, help="quantize key input activation to qk mult")
    model_group.add_argument("--quantize_attn_act_softmax_input", action=argparse.BooleanOptionalAction, default=False, help="quantize input activation to softmax")
    model_group.add_argument("--quantize_attn_act_pv_mult_p_input", action=argparse.BooleanOptionalAction, default=False, help="quantize softmax input activation to pv mult")
    model_group.add_argument("--quantize_attn_act_pv_mult_v_input", action=argparse.BooleanOptionalAction, default=False, help="quantize value input activation to pv mult")
    model_group.add_argument("--quantize_attn_act_pv_mult_output", action=argparse.BooleanOptionalAction, default=False, help="quantize output activation of pv_mult")
    model_group.add_argument("--quantize_attn_act_output", action=argparse.BooleanOptionalAction, default=False, help="quantize output activation of attention")

    ### Default Precisions for Attention Activations
    model_group.add_argument("--quantize_attn_act_bits", type=int, default=8, help="number of bits for attn quantization")

    ### Overrides for granular Attention Activatinos
    model_group.add_argument("--quantize_attn_act_input_bits", type=int, default=None, help="number of bits for attention input quantization")
    model_group.add_argument("--quantize_attn_act_qk_mult_q_input_bits", type=int, default=None, help="number of bits for qk mult query input quantization")
    model_group.add_argument("--quantize_attn_act_qk_mult_k_input_bits", type=int, default=None, help="number of bits for qk mult key input quantization")
    model_group.add_argument("--quantize_attn_act_softmax_input_bits", type=int, default=None, help="number of bits for softmax input quantization")
    model_group.add_argument("--quantize_attn_act_pv_mult_p_input_bits", type=int, default=None, help="number of bits for pv mult softmax input quantization")
    model_group.add_argument("--quantize_attn_act_pv_mult_v_input_bits", type=int, default=None, help="number of bits for pv mult value input quantization")
    model_group.add_argument("--quantize_attn_act_pv_mult_output_bits", type=int, default=None, help="number of bits for pv mult output quantization")
    model_group.add_argument("--quantize_attn_act_output_bits", type=int, default=None, help="number of bits for attention output quantization")

    ### Whether to use MLP Activations
    model_group.add_argument("--quantize_mlp_act", action=argparse.BooleanOptionalAction, default=False, help="quantize all input/output activations in mlp")
    model_group.add_argument("--quantize_mlp_act_input", action=argparse.BooleanOptionalAction, default=False, help="quantize input activation to mlp")
    model_group.add_argument("--quantize_mlp_act_activation_input", action=argparse.BooleanOptionalAction, default=False, help="quantize input activation to activation function")
    model_group.add_argument("--quantize_mlp_act_activation_output", action=argparse.BooleanOptionalAction, default=False, help="quantize output activation of activation function")
    model_group.add_argument("--quantize_mlp_act_output", action=argparse.BooleanOptionalAction, default=False, help="quantize output activation of mlp")

    ### Default Precisions for MLP Activations
    model_group.add_argument("--quantize_mlp_act_bits", type=int, default=8, help="number of bits for mlp quantization")

    ### Overrides for granular MLP Activatinos
    model_group.add_argument("--quantize_mlp_act_input_bits", type=int, default=None, help="number of bits for mlp input quantization")
    model_group.add_argument("--quantize_mlp_act_activation_input_bits", type=int, default=None, help="number of bits for activation function input quantization")
    model_group.add_argument("--quantize_mlp_act_activation_output_bits", type=int, default=None, help="number of bits for activation function output quantization")
    model_group.add_argument("--quantize_mlp_act_output_bits", type=int, default=None, help="number of bits for mlp output quantization")

    ### Whether activations should be saved
    model_group.add_argument("--store_activations", action=argparse.BooleanOptionalAction, default=False, help="whether the activations should be saved as a buffer and updated through training")

    ## Linear Attn Weight Quantization Precision and Method

    ### Default methods and precisions
    model_group.add_argument("--quantize_linear_method", type=str, default="affine_quant", choices=quant_methods, help="function used for linear quantization")
    model_group.add_argument("--quantize_linear_bits", type=int, default=8, help="number of bits for linear quantization")

    #### Overrides for granular Methods and Precisions
    model_group.add_argument("--quantize_linear_attn_q_method", type=str, default=None, choices=quant_methods, help="function used for c_attn_q quantization")
    model_group.add_argument("--quantize_linear_attn_q_bits", type=int, default=None, help="number of bits for c_attn_q quantization")

    model_group.add_argument("--quantize_linear_attn_k_method", type=str, default=None, choices=quant_methods, help="function used for c_attn_k quantization")
    model_group.add_argument("--quantize_linear_attn_k_bits", type=int, default=None, help="number of bits for c_attn_k quantization")

    model_group.add_argument("--quantize_linear_attn_v_method", type=str, default=None, choices=quant_methods, help="function used for c_attn_v quantization")
    model_group.add_argument("--quantize_linear_attn_v_bits", type=int, default=None, help="number of bits for c_attn_v quantization")

    model_group.add_argument("--quantize_linear_attn_proj_method", type=str, default=None, choices=quant_methods, help="function used for c_proj in attention quantization")
    model_group.add_argument("--quantize_linear_attn_proj_bits", type=int, default=None, help="number of bits for c_proj in attention quantization")

    #### Overrides for Linear MLP Weight Quantization Precision and Method
    model_group.add_argument("--quantize_linear_mlp_up_method", type=str, default=None, choices=quant_methods, help="function used for mlp_up quantization")
    model_group.add_argument("--quantize_linear_mlp_up_bits", type=int, default=None, help="number of bits for mlp_up quantization")
    model_group.add_argument("--quantize_linear_mlp_down_method", type=str, default=None, choices=quant_methods, help="function used for mlp_down quantization")
    model_group.add_argument("--quantize_linear_mlp_down_bits", type=int, default=None, help="number of bits for mlp_down quantization")

    ## Quantized Linear Warmup Iterations -- how many to first use regular linear, before switching to quantized
    model_group.add_argument("--quantization_warmup_iters", type=int, default=100)

    # POSITIONAL EMBEDDING VARIATIONS
    model_group.add_argument('--use_rotary_embeddings', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--sym_rot_num_angles', type=int, default=512, help="number of angles to use for symmetric rope variant")
    model_group.add_argument("--rope_variant", type=str, default="rope", choices=["rope", "soap"])
    model_group.add_argument("--rope_length", type=int, default=None, help="Defaults to all embeddings (if set to None), else must be even.")
    model_group.add_argument('--use_abs_pos_embeddings', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--use_fire_embeddings', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--shared_fire_embeddings', default=False, action=argparse.BooleanOptionalAction)

    ## Positional Embedding Weight Initialization Options
    model_group.add_argument( "--embedding_mean_init", type=float, default=0.0)
    model_group.add_argument( "--embedding_std_init", type=float, default=0.02)

    ## FIRE Options (Functional Interpolation for Relative Positional Encoding)
    model_group.add_argument( "--fire_log_bias", type=float, default=1.0, help="bias in the function psi(x) = log(cx + bias)")
    model_group.add_argument( "--fire_num_hidden_layers", type=int, default=1, help="number of hidden layers (sigmas) in mlp in FIRE without counting outermost sigma")
    model_group.add_argument( "--fire_mlp_width", type=int, default=32, help="mlp_width: one hidden dimension of linear layers in mlp in FIRE")
    model_group.add_argument( "--fire_init_c", type=float, default=0.1, help="init_c: initial value of log transformation parameter c in FIRE")
    model_group.add_argument( "--fire_init_L", type=float, default=512.0, help="init_L: initial value of threshold L in FIRE (fixed values without L_multiplier)")
    model_group.add_argument( "--fire_outermost_sigma", type=bool, default=False, action=argparse.BooleanOptionalAction, help="whether or not adding outermost sigma in mlp in FIRE")

    # SOFTMAX VARIATIONS
    softmax_variations = [
        "saturatingconsmax",
        "consmax",
        "consmax_v2",
        "consmax_quan",
        "polymax",
        "relumax",
        "relu2max",
        "sigmoidmax",
        "vpolymax",
        "exppolymax",
        "strongermax",
        "softermax",
        "sigsoftmax",
        "softmax",
        "softplus",
        "squareplus",
        "exppolymax",
        ]

    ## Selection of softmax variation for attention and output layers
    model_group.add_argument("--softmax_variant_attn", type=str, default="softmax", choices=softmax_variations)
    model_group.add_argument("--softmax_variant_output", type=str, default="softmax", choices=softmax_variations)
    model_group.add_argument("--disable_flash_attention", default=False, action=argparse.BooleanOptionalAction, help="manual setting to disable flash attention")

    ## Custom Softmax Variation Options
    ### ConSmax and SaturatingConSmax Options
    model_group.add_argument("--consmax_initial_beta", type=float, default=2.5)
    model_group.add_argument("--consmax_initial_gamma", type=float, default=100.0)
    model_group.add_argument('--consmax_use_euler_base', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--consmax_base", type=float, default=2.0)

    ### Special Options for ConSmaxV2
    model_group.add_argument("--consmax_per_head", default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--consmax_v2_clamping", default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--consmax_v2_clamp_value", type=float, default=80.0, help="maximum value to clamp inputs")

    ### Special Options for SaturatingConSmax
    model_group.add_argument("--consmax_saturation", type=float, default=11.0, help="point where we transition from consmax to linear saturatingconsmax, defaults to 11 to approximate e^x sat for fp16")
    model_group.add_argument('--consmax_learnable_beta', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--consmax_learnable_gamma', default=True, action=argparse.BooleanOptionalAction)

    ### Polymax Options
    model_group.add_argument("--polymax_x_intercept", type=float, default=-100.0)
    model_group.add_argument("--polymax_y_intercept", type=float, default=1.0)
    model_group.add_argument("--polymax_power", type=float, default=2.0)
    model_group.add_argument("--polymax_divisor", type=float, default=1000.0)

    ### ReLUMax Options
    model_group.add_argument("--relumax_divisor", type=float, default=256.0)

    ### ReLU2Max Options
    model_group.add_argument("--relu2max_divisor", type=float, default=256.0)

    ### SimgoidMax Options
    model_group.add_argument("--sigmoidmax_divisor", type=float, default=256.0)

    ### SigSoftmax Options
    model_group.add_argument('--sigsoftmax_use_euler_base', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--sigsoftmax_base", type=float, default=2.0)

    ### Strongermax Options - Testing Incremental Adjustments to Regular Softmax
    model_group.add_argument("--strongermax_strength", type=float, default=math.e)
    model_group.add_argument('--strongermax_div_by_sum_of_terms', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--strongermax_divisor", type=float, default=1.0)
    model_group.add_argument('--strongermax_use_xmax', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--strongermax_xmax_guess', type=float, default=None)
    model_group.add_argument('--strongermax_overflow_recompute', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--strongermax_overflow_recompute_value', type=float, default=88.0)

    ### Strongermax Clamping
    model_group.add_argument('--strongermax_clamping', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--strongermax_clamp_value', type=float, default=88.0)

    ### From https://www.evanmiller.org/attention-is-off-by-one.html
    model_group.add_argument('--strongermax_obo', type=float, default=0.0)
    model_group.add_argument('--strongermax_use_learned_obo', default=False, action=argparse.BooleanOptionalAction)
    model_group.add_argument('--strongermax_use_learned_obo_per_head', default=False, action=argparse.BooleanOptionalAction)

    ### Temperature adjustment factor
    model_group.add_argument('--strongermax_temperature_factor', type=float, default=1.0)
    model_group.add_argument('--strongermax_use_learned_temperature_factor', default=False, action=argparse.BooleanOptionalAction)

    ### ExpPolymax Options
    model_group.add_argument('--exppolymax_use_euler_base', default=True, action=argparse.BooleanOptionalAction)
    model_group.add_argument("--exppolymax_base", type=float, default=4.0)
    model_group.add_argument("--exppolymax_y_intercept", type=float, default=1.0)
    model_group.add_argument("--exppolymax_power", type=float, default=2.0)
    model_group.add_argument("--exppolymax_divisor", type=float, default=1000.0)

    ### Softermax Specific Options
    model_group.add_argument('--softermax_use_xmax', default=True, action=argparse.BooleanOptionalAction)

    ### SoftPlus Options
    model_group.add_argument('--softplus_divisor', type=float,default=100.0)
    ### SquarePlus Options
    model_group.add_argument('--squareplus_divisor', type=float,default=100.0)

    ### Sequence Length Division https://arxiv.org/abs/2309.
    model_group.add_argument('--div_by_seq_len', default=False, action=argparse.BooleanOptionalAction)

    # Gradient Checkpointing
    model_group.add_argument('--use_gradient_checkpointing', default=False, action=argparse.BooleanOptionalAction, help="Memory efficient training, but takes longer time to train due to trading compute time for memory efficiency. For best memory tradeoff omit the --compile flag. For medium memory tradeoff add --compile.")
    model_group.add_argument('--recompute_backward_pass', default=False, action=argparse.BooleanOptionalAction, help="Recomputes for the backward pass, must use with --use_gradient_checkpointing")

    # Optimizer args
    training_group.add_argument('--max_iters', default=3500, type=int)
    training_group.add_argument('--weight_decay', default=1e-1, type=float)
    training_group.add_argument('--beta1', default=0.9, type=float)
    training_group.add_argument('--beta2', default=0.99, type=float)
    training_group.add_argument('--grad_clip', default=1.0, type=float)

    # LR schedule args
    training_group.add_argument('--learning_rate', default=1e-3, type=float)
    training_group.add_argument('--min_lr', default=1e-4, type=float)
    training_group.add_argument('--decay_lr', default=False, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--lr_decay_iters', default=3500, type=int)
    training_group.add_argument('--lr_decay_match_max_iters', default=True, action=argparse.BooleanOptionalAction)
    training_group.add_argument('--warmup_iters', default=100, type=int)

    # DDP args
    training_group.add_argument('--backend', default='nccl', type=str)
    training_group.add_argument('--gradient_accumulation_steps', default=1, type=int)

    # System args
    training_group.add_argument('--device', default='cuda', type=str)
    training_group.add_argument("--dtype", type=str, default="float16", choices=["bfloat16", "float16", "float32"], help="torch data type for inference, e.g. 'int8'")
    training_group.add_argument('--compile', default=False, action=argparse.BooleanOptionalAction)

    # Logging args
    logging_group.add_argument('--log_project', default='out-test', type=str)
    logging_group.add_argument('--log_run_name', default='logs-test', type=str)
    logging_group.add_argument('--timestamp', default='', type=str)

    # Module And Parameter Logging and Plots of Summary Statistics
    model_group.add_argument('--softmax_io_logging', default=False, action=argparse.BooleanOptionalAction, help="logs inputs and outputs of supported softmaxes")
    model_group.add_argument('--softmax_io_log_interval', default=1, type=int)
    model_group.add_argument('--consmax_beta_gamma_logging', default=False, action=argparse.BooleanOptionalAction, help="logs beta and gamma")
    logging_group.add_argument('--create_statistics', default=False, action=argparse.BooleanOptionalAction)
    logging_group.add_argument('--plot_statistics', default=False, action=argparse.BooleanOptionalAction)

    # CSV logging
    logging_group.add_argument('--csv_log', default=True, action=argparse.BooleanOptionalAction)
    logging_group.add_argument('--csv_dir', default='csv_logs', type=str)
    logging_group.add_argument('--csv_name', default='output', type=str, help="Output csv basename. Note, the .csv will be automatically appended.")

    # Tensorboard args
    logging_group.add_argument('--tensorboard_log', default=True, action=argparse.BooleanOptionalAction)
    logging_group.add_argument('--tensorboard_log_dir', type=str, default='logs')
    logging_group.add_argument('--tensorboard_run_name', type=str, default='logs-test')
    logging_group.add_argument('--tensorboard_graph', default=True, action=argparse.BooleanOptionalAction)

    ## Export Model graph
    logging_group.add_argument('--export_model_graph', default=False, action=argparse.BooleanOptionalAction, help="exports tensorboard model of graph")

    # Onnx args
    logging_group.add_argument('--onnx_output', default=False, action=argparse.BooleanOptionalAction)

    # Wandb args
    logging_group.add_argument('--wandb_log', default=False, action=argparse.BooleanOptionalAction)
    logging_group.add_argument('--wandb_project', type=str, default='out-test')
    logging_group.add_argument('--wandb_run_name', type=str, default='logs-test')

    ### Create model from json config file & save config file to json
    logging_group.add_argument('--load_config_json', type=str, help="Option to load model parameters from existing json file")
    logging_group.add_argument('--save_config_json', type=str, help="Option to save model parameters as new config json file")

    # Visualization args
    logging_group.add_argument('--statistic', choices=[ 'input_mean', 'input_median', 'input_stdev', 'input_max', 'input_min', 'output_mean', 'output_median', 'output_stdev', 'output_max', 'output_min', 'all_stats', 'input_all','output_all' ], default='input_mean', help='Select one or all statistics to display, e.g., --statistic input_min, or --statistic all_stats')
    logging_group.add_argument('--graph_type', choices=[ "heatmap", "plot", "boxplot", "all" ], default='no_graph', help='Select one of the graph types to display, e.g., --graph_type heatmap, or --graph_type plot')
    logging_group.add_argument('--box_plot_interval', default=1000, type=int, help='Instead of using mean/median/stdev statistics, create box plot of all input/output values at certain intervals of iteration')
    logging_group.add_argument('--box_plot_statistic', choices=['input', 'output', 'all'], default='', help='Select input or output statistic to display in boxplot')

    # Model Parameter Distribution
    logging_group.add_argument('--print_model_info', default=True, action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    if args.load_config_json is not None:
        with open(args.load_config_json, 'r') as config_file:
            config = json.load(config_file)

        # Update the args namespace with values from the JSON file
        for key, value in config.items():
            setattr(args, key, value)

    # Save all params to provided json if flag is present
    if args.save_config_json is not None:
        with open(args.save_config_json, 'w') as json_file:
            json.dump(vars(args), json_file)

    return args, model_group, training_group, logging_group

class FlattenListAction(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
        # For each value passed, split it by whitespace (if any) and convert each token to float.
        result = []
        for v in values:
            # If the value contains spaces, split it, otherwise just use the value.
            tokens = v.split() if " " in v else [v]
            result.extend([float(x) for x in tokens])
        setattr(namespace, self.dest, result)
